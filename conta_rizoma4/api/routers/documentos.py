# -*- coding: utf-8 -*-
"""Endpoints de documentos (subida al CAS de rizoma4)."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from ...custodia.repositorios import RepositorioDocumento
from ...custodia.repositorios import RepositorioObra
from ..rizoma4_client import ClienteRizoma4, Rizoma4Error
from .auth import requerir_usuario


router = APIRouter(prefix="/documentos", tags=["documentos"])
MAX_DOCUMENTO_BYTES = 20 * 1024 * 1024


@router.post("", status_code=201)
async def subir(
    tipo: str = Form(...),
    obra_id: Optional[str] = Form(None),
    subido_por: Optional[str] = Form(None),
    fichero: UploadFile = File(...),
    usuario: dict = Depends(requerir_usuario),
):
    empresa_id = usuario.get("empresa_id")
    if not empresa_id:
        raise HTTPException(status_code=403, detail="Usuario sin empresa asociada en el token")

    contenido = await fichero.read(MAX_DOCUMENTO_BYTES + 1)
    if len(contenido) > MAX_DOCUMENTO_BYTES:
        raise HTTPException(status_code=413, detail="El documento supera el límite de 20 MiB")
    if obra_id is not None:
        obra = RepositorioObra().obtener(obra_id)
        if obra is None or obra.get("empresa_id") != empresa_id:
            raise HTTPException(status_code=404, detail="Obra no encontrada para esta empresa")
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
        tamano_bytes=len(contenido),
        subido_por=str(usuario.get("sub") or usuario.get("usuario_id")),
    )
    return doc
