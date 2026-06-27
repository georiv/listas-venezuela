"""Gemini multimodal extraction: photo -> structured patient rows.

Single call replaces the old Google Vision OCR + Claude parsing pipeline.
Uses Gemini Flash by default and escalates to Gemini Pro when Flash's result
looks low quality (no rows, or too many rows missing required fields).
"""
import json
import os
import re

from google import genai
from google.genai import types
from pydantic import BaseModel

FLASH_MODEL = os.environ.get("GEMINI_FLASH_MODEL", "gemini-2.5-flash")
PRO_MODEL = os.environ.get("GEMINI_PRO_MODEL", "gemini-2.5-pro")

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# Fraction of rows allowed to be missing nombre/apellido before we escalate.
QUALITY_THRESHOLD = 0.3


class Persona(BaseModel):
    nombre: str
    apellido: str
    cedula: str = ""
    centro: str = ""
    edad_sector: str = ""


SYSTEM_PROMPT = """\
Eres un asistente que lee fotos de listas hospitalarias y de evacuación \
escritas a mano en Venezuela, y extrae los datos de cada persona.

Las listas suelen tener uno de estos formatos:
1. Numeradas: "1. Nombre Apellido edad" — el hospital/centro aparece en el \
   ENCABEZADO de la hoja y aplica a TODAS las filas.
2. Por apellido: "Apellido Nombre → sector/destino" — el nombre puede venir \
   después del apellido, y la flecha indica un sector, barrio o destino.

Extrae para cada persona estos campos:
- nombre: nombre(s) de pila.
- apellido: apellido(s). El orden nombre/apellido varía entre listas; usa tu \
  criterio (los nombres venezolanos suelen tener 1-2 nombres y 1-2 apellidos).
- cedula: cédula venezolana en formato "V-12345678" (letra de nacionalidad \
  V o E, un guion, y los dígitos SIN puntos). Muchas listas NO tienen cédula: \
  en ese caso deja "".
- centro: hospital o centro de salud. Si está en el encabezado, aplícalo a TODAS \
  las filas. Si no hay, deja "".
- edad_sector: la edad y/o el sector/barrio/destino/ubicación.
    * EDAD: escribe SOLO el número, sin "años" ni "a" (ej.: "10", NO "10 años").
    * Si la edad está en MESES, usa el número seguido de "m" (ej.: "22m"), para
      no confundirla con años.
    * El sector o ubicación (La Guaira, Pasillo 1, etc.) se escribe como texto.
      Si hay edad y ubicación, combínalas con " · " (ej.: "9 · Pasillo 1").
    * Si no hay nada, deja "".

Reglas:
- Extrae TODAS las personas legibles de la lista.
- Campos OBLIGATORIOS: nombre, apellido y centro. cedula y edad_sector son
  OPCIONALES (es válido y correcto dejarlas en "").
- No incluyas a una persona si no logras leer su nombre.
- Si la foto contiene varias hojas, prioriza la lista más completa y legible.
- No inventes datos que no estén en la imagen. Lo que no sepas, déjalo en "".
- Conserva tildes y la ortografía de los nombres tal como se leen.
"""


async def _call(model: str, image_bytes: bytes, mime_type: str, user_text: str):
    return await client.aio.models.generate_content(
        model=model,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            user_text,
        ],
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=list[Persona],
            temperature=0,
        ),
    )


def _records_from(resp) -> list[dict]:
    """Pull rows out of a Gemini response (parsed schema, with text fallback)."""
    parsed = getattr(resp, "parsed", None)
    if parsed:
        return [p.model_dump() for p in parsed]
    if resp.text:
        return [Persona(**d).model_dump() for d in json.loads(resp.text)]
    return []


def _complete_rows(records: list[dict]) -> int:
    return sum(1 for r in records if r["nombre"].strip() and r["apellido"].strip())


def _quality_ok(records: list[dict]) -> bool:
    if not records:
        return False
    missing = len(records) - _complete_rows(records)
    return (missing / len(records)) <= QUALITY_THRESHOLD


def _clean_cedula(value: str) -> str:
    """Normalize to the site's "V-12345678" format (or "" when absent)."""
    s = str(value).upper()
    digits = "".join(c for c in s if c.isdigit())
    if not digits:
        return ""
    m = re.search(r"[VEJGP]", s)  # Venezuelan nationality letters
    return f"{m.group(0)}-{digits}" if m else digits


def _normalize(records: list[dict]) -> list[dict]:
    # Drop rows with no readable name; they cannot be used.
    records = [r for r in records if r.get("nombre", "").strip()]
    for r in records:
        r["cedula"] = _clean_cedula(r.get("cedula", ""))
    return records


async def extract_records(
    image_bytes: bytes,
    mime_type: str,
    centro_hint: str = "",
) -> list[dict]:
    """Extract patient rows from a list photo. Flash first, Pro on low quality."""
    user_text = "Extrae todas las personas de esta lista hospitalaria."
    if centro_hint:
        user_text += f" Centro de salud de referencia: {centro_hint}."

    # 1. Try the cheap model first.
    flash_records: list[dict] = []
    try:
        flash_records = _records_from(await _call(FLASH_MODEL, image_bytes, mime_type, user_text))
    except Exception:
        flash_records = []

    if _quality_ok(flash_records):
        return _normalize(flash_records)

    # 2. Escalate to Pro; keep whichever result has more complete rows.
    try:
        pro_records = _records_from(await _call(PRO_MODEL, image_bytes, mime_type, user_text))
    except Exception:
        pro_records = []

    best = pro_records if _complete_rows(pro_records) >= _complete_rows(flash_records) else flash_records
    return _normalize(best)
