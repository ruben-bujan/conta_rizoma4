# -*- coding: utf-8 -*-
"""Endpoints de obras."""
from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ...custodia.modelo import Obra
from ...custodia.repositorios import RepositorioObra
from .auth import requerir_usuario, requerir_roles


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
def crear(
    entrada: ObraIn,
    usuario: dict = Depends(requerir_roles("admin")),
):
    empresa_id = usuario.get("empresa_id")
    if not empresa_id:
        raise HTTPException(status_code=403, detail="Usuario sin empresa asociada en el token")
    
    entrada.empresa_id = empresa_id
    obra = Obra(**entrada.model_dump())
    return RepositorioObra().crear(obra).__dict__


@router.get("")
def listar(
    usuario: dict = Depends(requerir_usuario),
):
    empresa_id = usuario.get("empresa_id")
    if not empresa_id:
        raise HTTPException(status_code=403, detail="Usuario sin empresa asociada en el token")
    return RepositorioObra().listar(empresa_id)


@router.get("/{obra_id}")
def obtener(
    obra_id: str,
    usuario: dict = Depends(requerir_usuario),
):
    empresa_id = usuario.get("empresa_id")
    if not empresa_id:
        raise HTTPException(status_code=403, detail="Usuario sin empresa asociada en el token")
    
    d = RepositorioObra().obtener(obra_id)
    if d is None:
        raise HTTPException(status_code=404, detail="Obra no encontrada")
        
    if d.get("empresa_id") != empresa_id:
        raise HTTPException(status_code=404, detail="Obra no encontrada")
        
    return d
