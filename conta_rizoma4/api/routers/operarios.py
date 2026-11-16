# -*- coding: utf-8 -*-
"""Endpoints de operarios."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ...custodia.modelo import Operario
from ...custodia.repositorios import RepositorioOperario


router = APIRouter(prefix="/operarios", tags=["operarios"])


class OperarioIn(BaseModel):
    operario_id: str
    empresa_id: str
    nombre: str
    rol: str
    email: Optional[str] = None
    certificado: Optional[str] = None


@router.post("", status_code=201)
def crear(entrada: OperarioIn):
    op = Operario(**entrada.model_dump())
    return RepositorioOperario().crear(op).__dict__


@router.get("")
def listar(empresa_id: str = Query(...)):
    return RepositorioOperario().listar(empresa_id)


@router.get("/{operario_id}")
def obtener(operario_id: str):
    d = RepositorioOperario().obtener(operario_id)
    if d is None:
        raise HTTPException(status_code=404, detail="Operario no encontrado")
    return d
