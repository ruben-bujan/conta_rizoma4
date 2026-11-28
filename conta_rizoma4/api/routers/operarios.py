# -*- coding: utf-8 -*-
"""Endpoints de operarios."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ...custodia.modelo import Operario
from ...custodia.repositorios import RepositorioOperario
from .auth import requerir_usuario, requerir_roles


router = APIRouter(prefix="/operarios", tags=["operarios"])


class OperarioIn(BaseModel):
    operario_id: str
    empresa_id: str
    nombre: str
    rol: str
    email: Optional[str] = None
    certificado: Optional[str] = None


@router.post("", status_code=201)
def crear(
    entrada: OperarioIn,
    usuario: dict = Depends(requerir_roles("admin")),
):
    empresa_id = usuario.get("empresa_id")
    if not empresa_id:
        raise HTTPException(status_code=403, detail="Usuario sin empresa asociada en el token")
    
    entrada.empresa_id = empresa_id
    op = Operario(**entrada.model_dump())
    return RepositorioOperario().crear(op).__dict__


@router.get("")
def listar(
    usuario: dict = Depends(requerir_usuario),
):
    empresa_id = usuario.get("empresa_id")
    if not empresa_id:
        raise HTTPException(status_code=403, detail="Usuario sin empresa asociada en el token")
    return RepositorioOperario().listar(empresa_id)


@router.get("/{operario_id}")
def obtener(
    operario_id: str,
    usuario: dict = Depends(requerir_usuario),
):
    empresa_id = usuario.get("empresa_id")
    if not empresa_id:
        raise HTTPException(status_code=403, detail="Usuario sin empresa asociada en el token")
    
    d = RepositorioOperario().obtener(operario_id)
    if d is None:
        raise HTTPException(status_code=404, detail="Operario no encontrado")
    
    # Validar aislamiento estricto por empresa
    if d.get("empresa_id") != empresa_id:
        raise HTTPException(status_code=404, detail="Operario no encontrado")
        
    return d
