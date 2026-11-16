# -*- coding: utf-8 -*-
"""Endpoints de leases (reserva de índices)."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ...custodia.repositorios import RepositorioLease
from ...custodia.modelo import CustodiaError


router = APIRouter(prefix="/leases", tags=["leases"])


class LeaseSolicitarIn(BaseModel):
    empresa_id: str
    obra_id: Optional[str] = None
    tipo: str = "asiento"
    operario: str
    duracion_min: int = 1440


@router.post("", status_code=201)
def solicitar(entrada: LeaseSolicitarIn):
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
def obtener(lease_id: str):
    lease = RepositorioLease().obtener(lease_id)
    if lease is None:
        raise HTTPException(status_code=404, detail="Lease no encontrado")
    return lease


class LeaseRenovarIn(BaseModel):
    duracion_min: int = 1440


@router.post("/{lease_id}/renovar")
def renovar(lease_id: str, entrada: LeaseRenovarIn):
    try:
        return RepositorioLease().renovar(lease_id, entrada.duracion_min)
    except CustodiaError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/{lease_id}/cancelar")
def cancelar(lease_id: str):
    repo = RepositorioLease()
    if repo.obtener(lease_id) is None:
        raise HTTPException(status_code=404, detail="Lease no encontrado")
    repo.cancelar(lease_id)
    return {"ok": True}
