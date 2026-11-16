# -*- coding: utf-8 -*-
"""Endpoints de autenticación."""
from __future__ import annotations

import os
from typing import Optional

import psycopg
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from ...auth import (
    AuthError, crear_token, hash_password, verificar_password,
    verificar_token,
)


router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)
PG_URL = os.environ.get(
    "CONTA_PG_URL",
    "postgresql://rizoma:rizoma_dev@localhost:5433/conta_rizoma4",
)


class RegistroIn(BaseModel):
    usuario_id: str
    email: str
    password: str
    nombre: str
    rol: str
    empresa_id: str


class LoginIn(BaseModel):
    email: str
    password: str


def _conn():
    return psycopg.connect(PG_URL)


@router.post("/registro", status_code=201)
def registro(entrada: RegistroIn):
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO usuarios (usuario_id, email, password_hash, "
                    "nombre, rol, empresa_id) VALUES (%s, %s, %s, %s, %s, %s)",
                    (entrada.usuario_id, entrada.email,
                     hash_password(entrada.password),
                     entrada.nombre, entrada.rol, entrada.empresa_id),
                )
            conn.commit()
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="Email ya registrado")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True, "usuario_id": entrada.usuario_id}


@router.post("/login")
def login(entrada: LoginIn):
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT usuario_id, password_hash, rol, empresa_id, activo "
                "FROM usuarios WHERE email = %s",
                (entrada.email,),
            )
            row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    usuario_id, hash_, rol, empresa_id, activo = row
    if not activo:
        raise HTTPException(status_code=403, detail="Usuario inactivo")
    if not verificar_password(entrada.password, hash_):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    token = crear_token(usuario_id, rol, empresa_id)
    return {"access_token": token, "token_type": "bearer",
            "usuario_id": usuario_id, "rol": rol, "empresa_id": empresa_id}


def usuario_actual(
    cred: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    if cred is None:
        return None
    try:
        payload = verificar_token(cred.credentials)
        return payload
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e))


def requerir_usuario(
    usuario: Optional[dict] = Depends(usuario_actual),
) -> dict:
    if usuario is None:
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    return usuario


@router.get("/me")
def me(usuario: dict = Depends(requerir_usuario)):
    return usuario
