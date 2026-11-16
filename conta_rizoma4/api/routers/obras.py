# -*- coding: utf-8 -*-
"""Endpoints de obras."""
from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ...custodia.modelo import Obra
from ...custodia.repositorios import RepositorioObra


router = APIRouter(prefix="/obras", tags=["obras"])


class ObraIn(BaseModel):
    obra_id: str
    empresa_id: str
    nombre: str
    cliente_nif: Optional[str] = None
    presupuesto_centimos: Optional[int] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None


@router.post("", status_code=201)
def crear(entrada: ObraIn):
    obra = Obra(**entrada.model_dump())
    return RepositorioObra().crear(obra).__dict__


@router.get("")
def listar(empresa_id: str = Query(...)):
    return RepositorioObra().listar(empresa_id)


@router.get("/{obra_id}")
def obtener(obra_id: str):
    d = RepositorioObra().obtener(obra_id)
    if d is None:
        raise HTTPException(status_code=404, detail="Obra no encontrada")
    return d
