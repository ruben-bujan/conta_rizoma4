# -*- coding: utf-8 -*-
"""Endpoint de verificación de cadena hash."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..schemas import VerificarIn, VerificarOut
from ...partida_doble import RepositorioAsiento
from .auth import requerir_usuario


router = APIRouter(prefix="/verificar", tags=["verificar"])


@router.post("", response_model=VerificarOut)
def verificar(
    entrada: VerificarIn,
    usuario: dict = Depends(requerir_usuario),
):
    empresa_id = usuario.get("empresa_id")
    if not empresa_id:
        raise HTTPException(status_code=403, detail="Usuario sin empresa asociada en el token")
    
    # Forzar que la verificación corresponda a la empresa del token autenticado
    entrada.empresa_id = empresa_id

    try:
        repo = RepositorioAsiento(entrada.empresa_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    rep = repo.verificar_cadena(desde=entrada.desde, hasta=entrada.hasta)
    return {
        "empresa_id": rep.empresa_id,
        "desde": rep.desde,
        "hasta": rep.hasta,
        "total": rep.total,
        "cadena_valida": rep.cadena_valida,
        "roturas": rep.roturas,
    }