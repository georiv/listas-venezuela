import asyncio
import uuid
import os
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Depends
from fastapi.responses import JSONResponse
from supabase import AsyncClient, acreate_client

from backend.services.parser import extract_records

router = APIRouter(prefix="/upload", tags=["ocr"])

ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp", "image/heic"}
MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB per image


async def get_supabase() -> AsyncClient:
    return await acreate_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_KEY"],
    )


async def _process_file(
    file: UploadFile,
    centro_hint: str,
    voluntario_id: str | None,
    supabase: AsyncClient,
) -> list[dict]:
    """Store one image and extract rows. Returns DB-ready dicts (not yet saved)."""
    image_bytes = await file.read()
    if len(image_bytes) > MAX_SIZE_BYTES:
        raise HTTPException(status_code=413, detail=f"{file.filename}: supera los 10 MB.")

    # 1. Store image in Supabase Storage
    object_name = f"{voluntario_id or 'anon'}/{uuid.uuid4()}-{file.filename}"
    await supabase.storage.from_("imagenes-listas").upload(
        object_name,
        image_bytes,
        {"content-type": file.content_type},
    )
    image_url = (
        f"{os.environ['SUPABASE_URL']}/storage/v1/object/imagenes-listas/{object_name}"
    )

    # 2. Extract structured rows straight from the image (Gemini multimodal,
    #    Flash with Pro fallback). No separate OCR step.
    records = await extract_records(image_bytes, file.content_type, centro_hint=centro_hint)
    return [
        {
            **r,
            "imagen_url": image_url,
            "estado": "pendiente",
            # null when no auth yet; the column is nullable so this is valid
            "voluntario_id": voluntario_id or None,
        }
        for r in records
    ]


@router.post("")
async def upload_images(
    files: list[UploadFile] = File(...),
    centro_hint: str = Form(""),
    # Optional for the open MVP (no login). Becomes a real auth.users UUID once
    # Supabase Auth is wired up.
    voluntario_id: str | None = Form(None),
    supabase: AsyncClient = Depends(get_supabase),
):
    valid = [f for f in files if f.content_type in ALLOWED_MIME]
    if not valid:
        raise HTTPException(
            status_code=415,
            detail="Ningún archivo es una imagen válida (JPG, PNG, WEBP o HEIC).",
        )

    # Process all images concurrently.
    results = await asyncio.gather(
        *(_process_file(f, centro_hint, voluntario_id, supabase) for f in valid),
        return_exceptions=True,
    )

    rows: list[dict] = []
    errores: list[str] = []
    for f, res in zip(valid, results):
        if isinstance(res, Exception):
            errores.append(f"{f.filename}: no se pudo procesar.")
        else:
            rows.extend(res)

    if not rows:
        raise HTTPException(
            status_code=422,
            detail="No se encontraron personas en las imágenes. Intente con fotos más claras.",
        )

    # Insert all rows from all images in one batch.
    result = await supabase.table("personas").insert(rows).execute()

    return JSONResponse(
        content={"records": result.data, "errores": errores},
        status_code=200,
    )
