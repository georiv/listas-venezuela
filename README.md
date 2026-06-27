# Listas Venezuela

Herramienta de emergencia para ayudar a las familias a localizar personas tras
el terremoto en Venezuela. Convierte **fotos de listas hospitalarias escritas a
mano** en archivos **CSV** compatibles con la carga masiva de
[hospitalesenvenezuela.com](https://hospitalesenvenezuela.com).

## ¿Cómo funciona?

1. Un voluntario sube una o varias fotos de listas de pacientes.
2. **Gemini** (multimodal) lee la letra manuscrita y extrae los datos en una
   sola llamada — sin paso de OCR aparte (usa `gemini-2.5-flash` y escala a
   `gemini-2.5-pro` cuando la calidad es baja).
3. El voluntario **revisa y corrige** los datos en una tabla editable.
4. La app exporta un **CSV** con el formato exacto del sitio.
5. El voluntario sube el CSV a hospitalesenvenezuela.com.

> Nada se exporta sin revisión humana. Los campos obligatorios son **nombre,
> apellido y centro**; la cédula y la edad/sector son opcionales.
>
> **Sin estado:** la app no guarda nada. Cada foto se procesa y el único
> resultado es el CSV que descarga el voluntario.

## Formato del CSV

```
nombre,apellido,cedula,centro,edad_sector
José Antonio,Pérez García,V-12345678,Hospital Universitario de Caracas,40 años · Petare
```

UTF-8 con BOM · separador coma · campos sin comillas salvo que contengan `,`/`"`.

## Stack

- **Frontend:** Nuxt 4 + Tailwind CSS (Vercel)
- **Backend:** FastAPI / Python (Railway) — sin base de datos
- **IA:** Google Gemini (lectura + estructuración en una sola llamada)

## Estructura

```
backend/          API FastAPI (subida múltiple + extracción con Gemini)
frontend/         App Nuxt (subida múltiple, tabla editable, exportación CSV)
```

## Desarrollo local

Requisitos: Python 3.11+, Node 20+ y una API key de
[Google AI Studio](https://aistudio.google.com/apikey).

```bash
# 1. Variables de entorno
cp .env.example .env        # y completa GEMINI_API_KEY

# 2. Backend
python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt
backend/.venv/bin/python -m uvicorn backend.main:app --reload   # http://localhost:8000

# 3. Frontend
cd frontend && npm install && npm run dev                        # http://localhost:3000
```

## Licencia

[MIT](LICENSE) — libre para usar, modificar y desplegar.
