# -*- coding: utf-8 -*-
"""Endpoints de documentos (subida al CAS de rizoma4)."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ...custodia.repositorios import RepositorioDocumento
from ..rizoma4_client import ClienteRizoma4, Rizoma4Error


router = APIRouter(prefix="/documentos", tags=["documentos"])


@router.post("", status_code=201)
async def subir(
    empresa_id: str = Form(...),
    tipo: str = Form(...),
    obra_id: Optional[str] = Form(None),
    subido_por: Optional[str] = Form(None),
    fichero: UploadFile = File(...),
):
    contenido = await fichero.read()
    # 1. Subir al CAS de rizoma4
    try:
        res = ClienteRizoma4().guardar_documento(
            empresa_id=empresa_id, contenido=contenido,
            nombre=fichero.filename or "",
        )
    except Rizoma4Error as e:
        raise HTTPException(status_code=503, detail=f"CAS no disponible: {e}")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"CAS error: {e}")

    hash_cas = res.get("hash_cas") or res.get("hash")
    if not hash_cas:
        raise HTTPException(status_code=500, detail="CAS no devolvió hash")

    # 2. Registrar en Postgres
    doc = RepositorioDocumento().crear(
        empresa_id=empresa_id, hash_cas=hash_cas, tipo=tipo,
        obra_id=obra_id, nombre=fichero.filename,
        tamano_bytes=len(contenido), subido_por=subido_por,
    )
    return doc
