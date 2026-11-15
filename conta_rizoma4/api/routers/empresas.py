# -*- coding: utf-8 -*-
"""Endpoints de empresas (de la config YAML)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..schemas import EmpresaOut
from ...config import get_config, get_empresa, ConfigError


router = APIRouter(prefix="/empresas", tags=["empresas"])


@router.get("", response_model=list[EmpresaOut])
def listar_empresas():
    cfg = get_config()
    return [e.a_dict() for e in cfg.empresas.values()]


@router.get("/{empresa_id}", response_model=EmpresaOut)
def obtener_empresa(empresa_id: str):
    try:
        e = get_empresa(empresa_id)
    except ConfigError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return e.a_dict()
