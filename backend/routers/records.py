import os
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from supabase import AsyncClient, acreate_client

router = APIRouter(prefix="/records", tags=["records"])


async def get_supabase() -> AsyncClient:
    return await acreate_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_KEY"],
    )


class PersonaUpdate(BaseModel):
    nombre: str | None = None
    apellido: str | None = None
    cedula: str | None = None
    centro: str | None = None
    edad_sector: str | None = None
    estado: str | None = None


@router.get("/search")
async def search(
    q: str = Query(..., min_length=2),
    supabase: AsyncClient = Depends(get_supabase),
):
    """Fuzzy name/cedula search using pg_trgm via RPC."""
    result = await supabase.rpc(
        "buscar_personas",
        {"query": q},
    ).execute()
    return result.data


@router.patch("/{record_id}")
async def update_record(
    record_id: str,
    body: PersonaUpdate,
    supabase: AsyncClient = Depends(get_supabase),
):
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No hay campos para actualizar.")

    result = (
        await supabase.table("personas")
        .update(updates)
        .eq("id", record_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Registro no encontrado.")
    return result.data[0]


@router.post("/{record_id}/approve")
async def approve(record_id: str, supabase: AsyncClient = Depends(get_supabase)):
    result = (
        await supabase.table("personas")
        .update({"estado": "aprobado"})
        .eq("id", record_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Registro no encontrado.")
    return result.data[0]
