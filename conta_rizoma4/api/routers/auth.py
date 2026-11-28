# -*- coding: utf-8 -*-
"""Endpoints de autenticación."""
from __future__ import annotations

from typing import Literal, Optional

import psycopg
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict

from ...auth import (
    AuthError, crear_token, hash_password, verificar_password,
    verificar_token,
)
from ...config.postgresql import PG_URL


router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)


class RegistroIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    usuario_id: str
    email: str
    password: str
    nombre: str
    rol: Literal["aux_obra", "visador", "aprobador"]


class LoginIn(BaseModel):
    email: str
    password: str


def _conn():
    return psycopg.connect(PG_URL)


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
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
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
        usuario_id = payload.get("sub")
        if not usuario_id:
            raise HTTPException(status_code=401, detail="Token sin identidad")
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT usuario_id, rol, empresa_id, activo FROM usuarios WHERE usuario_id = %s",
                    (usuario_id,),
                )
                row = cur.fetchone()
        if row is None or not row[3]:
            raise HTTPException(status_code=401, detail="Usuario inexistente o inactivo")
        return {
            "sub": row[0], "actor_id": row[0], "usuario_id": row[0],
            "rol": row[1], "empresa_id": row[2],
        }
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e))


def requerir_usuario(
    usuario: Optional[dict] = Depends(usuario_actual),
) -> dict:
    if usuario is None:
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    return usuario


def requerir_roles(*roles: str):
    def dependencia(usuario: dict = Depends(requerir_usuario)) -> dict:
        if usuario.get("rol") not in roles:
            raise HTTPException(status_code=403, detail="El rol no permite esta operación")
        return usuario
    return dependencia


@router.post("/registro", status_code=201)
def registro(entrada: RegistroIn, usuario: dict = Depends(requerir_usuario)):
    if usuario.get("rol") != "admin":
        raise HTTPException(status_code=403, detail="Se requiere rol admin para registrar usuarios")
    empresa_id = usuario.get("empresa_id")
    if not empresa_id:
        raise HTTPException(status_code=403, detail="El administrador no tiene empresa asociada")
    if not entrada.usuario_id.strip() or not entrada.nombre.strip() or not entrada.email.strip():
        raise HTTPException(status_code=422, detail="Identidad, nombre y email son obligatorios")
    if len(entrada.password) < 12:
        raise HTTPException(status_code=422, detail="La contraseña debe tener al menos 12 caracteres")
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO usuarios (usuario_id, email, password_hash, "
                    "nombre, rol, empresa_id) VALUES (%s, %s, %s, %s, %s, %s)",
                    (entrada.usuario_id, entrada.email,
                     hash_password(entrada.password),
                     entrada.nombre, entrada.rol, empresa_id),
                )
            conn.commit()
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="Email o usuario ya registrado")
    except Exception as e:
        raise HTTPException(status_code=503, detail="No se pudo completar el registro") from e
    return {"ok": True, "usuario_id": entrada.usuario_id, "empresa_id": empresa_id}


@router.get("/me")
def me(usuario: dict = Depends(requerir_usuario)):
    return usuario
