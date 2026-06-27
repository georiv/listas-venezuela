import asyncio
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

from backend.ratelimit import limiter
from backend.services.parser import extract_records

router = APIRouter(prefix="/upload", tags=["ocr"])

ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB per image


async def _process_file(file: UploadFile, centro_hint: str) -> list[dict]:
    """Extract rows from one image. Stateless — nothing is stored anywhere."""
    image_bytes = await file.read()
    if len(image_bytes) > MAX_SIZE_BYTES:
        raise HTTPException(status_code=413, detail=f"{file.filename}: supera los 10 MB.")
    return await extract_records(image_bytes, file.content_type, centro_hint=centro_hint)


@router.post("")
@limiter.limit("20/minute")
async def upload_images(
    request: Request,
    files: list[UploadFile] = File(...),
    centro_hint: str = Form(""),
):
    valid = [f for f in files if f.content_type in ALLOWED_MIME]
    if not valid:
        raise HTTPException(
            status_code=415,
            detail="Ningún archivo es una imagen válida (JPG, PNG o WEBP).",
        )

    # Process all images concurrently.
    results = await asyncio.gather(
        *(_process_file(f, centro_hint) for f in valid),
        return_exceptions=True,
    )

    records: list[dict] = []
    errores: list[str] = []
    for f, res in zip(valid, results):
        if isinstance(res, Exception):
            errores.append(f"{f.filename}: no se pudo procesar.")
        else:
            records.extend(res)

    if not records:
        raise HTTPException(
            status_code=422,
            detail="No se encontraron personas en las imágenes. Intente con fotos más claras.",
        )

    return JSONResponse(
        content={"records": records, "errores": errores},
        status_code=200,
    )
