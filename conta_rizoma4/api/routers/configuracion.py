# -*- coding: utf-8 -*-
"""Router de configuración con visado."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from ...config.config_json import cargar_config

router = APIRouter(prefix="/config", tags=["config"])


@router.get("")
def get_config():
    return cargar_config()


@router.post("/visa/admin")
def visa_admin(payload: dict):
    # placeholder: requiere visado del subdirector
    return {"ok": True, "visado": "subdirector", "payload": payload}


@router.post("/visa/user")
def visa_user(payload: dict):
    # placeholder: requiere visado del jefe de contabilidad
    return {"ok": True, "visado": "jefe_contabilidad", "payload": payload}
