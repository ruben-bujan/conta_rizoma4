# -*- coding: utf-8 -*-
"""Endpoints de leases (reserva de índices)."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from ...custodia.repositorios import RepositorioLease, RepositorioObra, RepositorioOperario
from ...custodia.modelo import CustodiaError
from .auth import requerir_usuario, requerir_roles


router = APIRouter(prefix="/leases", tags=["leases"])


class LeaseSolicitarIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    empresa_id: str
    obra_id: Optional[str] = None
    tipo: str = Field(default="asiento", min_length=1, max_length=40)
    operario: str = Field(min_length=1, max_length=100)
    duracion_min: int = Field(default=1440, ge=1, le=1440)


@router.post("", status_code=201)
def solicitar(
    entrada: LeaseSolicitarIn,
    usuario: dict = Depends(requerir_roles("admin")),
):
    empresa_id = usuario.get("empresa_id")
    if not empresa_id:
        raise HTTPException(status_code=403, detail="Usuario sin empresa asociada en el token")
    
    entrada.empresa_id = empresa_id
    operario = RepositorioOperario().obtener(entrada.operario)
    if operario is None or operario.get("empresa_id") != empresa_id or not operario.get("activo", True):
        raise HTTPException(status_code=404, detail="Operario no encontrado para esta empresa")
    if entrada.obra_id is not None:
        obra = RepositorioObra().obtener(entrada.obra_id)
        if obra is None or obra.get("empresa_id") != empresa_id:
            raise HTTPException(status_code=404, detail="Obra no encontrada para esta empresa")
    try:
        lease = RepositorioLease().solicitar(
            empresa_id=entrada.empresa_id, obra_id=entrada.obra_id,
            tipo=entrada.tipo, operario=entrada.operario,
            duracion_min=entrada.duracion_min,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return lease


@router.get("/{lease_id}")
def obtener(
    lease_id: str,
    usuario: dict = Depends(requerir_usuario),
):
    empresa_id = usuario.get("empresa_id")
    if not empresa_id:
        raise HTTPException(status_code=403, detail="Usuario sin empresa asociada en el token")
        
    lease = RepositorioLease().obtener(lease_id)
    if lease is None:
        raise HTTPException(status_code=404, detail="Lease no encontrado")
        
    if lease.get("empresa_id") != empresa_id:
        raise HTTPException(status_code=404, detail="Lease no encontrado")
        
    return lease


class LeaseRenovarIn(BaseModel):
    duracion_min: int = Field(default=1440, ge=1, le=1440)


@router.post("/{lease_id}/renovar")
def renovar(
    lease_id: str,
    entrada: LeaseRenovarIn,
    usuario: dict = Depends(requerir_roles("admin")),
):
    empresa_id = usuario.get("empresa_id")
    if not empresa_id:
        raise HTTPException(status_code=403, detail="Usuario sin empresa asociada en el token")
        
    lease = RepositorioLease().obtener(lease_id)
    if lease is None or lease.get("empresa_id") != empresa_id:
        raise HTTPException(status_code=404, detail="Lease no encontrado")

    try:
        return RepositorioLease().renovar(lease_id, entrada.duracion_min)
    except CustodiaError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/{lease_id}/cancelar")
def cancelar(
    lease_id: str,
    usuario: dict = Depends(requerir_roles("admin")),
):
    empresa_id = usuario.get("empresa_id")
    if not empresa_id:
        raise HTTPException(status_code=403, detail="Usuario sin empresa asociada en el token")
        
    repo = RepositorioLease()
    lease = repo.obtener(lease_id)
    if lease is None or lease.get("empresa_id") != empresa_id:
        raise HTTPException(status_code=404, detail="Lease no encontrado")
        
    repo.cancelar(lease_id)
    return {"ok": True}
