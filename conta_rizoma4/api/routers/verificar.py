# -*- coding: utf-8 -*-
"""Endpoint de verificación de cadena hash."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..schemas import VerificarIn, VerificarOut
from ...partida_doble import RepositorioAsiento


router = APIRouter(prefix="/verificar", tags=["verificar"])


@router.post("", response_model=VerificarOut)
def verificar(entrada: VerificarIn):
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
