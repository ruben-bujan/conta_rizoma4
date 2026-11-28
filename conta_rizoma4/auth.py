# -*- coding: utf-8 -*-
"""Autenticación: JWT + Argon2id."""
from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


JWT_SECRET = os.environ.get("CONTA_JWT_SECRET") or secrets.token_urlsafe(48)
JWT_ALGORITHM = "HS256"

# Guardia: el secreto de desarrollo no puede usarse en producción.
# Reutiliza los marcores ya definidos en scripts/demo_completo.py.
_PROD_MARKERS = ("prod", "production", "-live", "_live", "prd")
_pg_signal = (
    os.environ.get("CONTA_PG_URL", "") + " " + os.environ.get("CONTA_PG_DB", "")
).lower()
if "CONTA_JWT_SECRET" not in os.environ and any(m in _pg_signal for m in _PROD_MARKERS):
    raise RuntimeError(
        "CONTA_JWT_SECRET no configurado: debe definirse antes de iniciar "
        "la aplicación en producción."
    )
if len(JWT_SECRET.encode("utf-8")) < 32:
    raise RuntimeError("CONTA_JWT_SECRET debe tener al menos 32 bytes")
JWT_EXPIRACION_MIN = 60 * 24  # 24 horas

_hasher = PasswordHasher()


class AuthError(Exception):
    pass


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verificar_password(password: str, hash_: str) -> bool:
    try:
        _hasher.verify(hash_, password)
        return True
    except VerifyMismatchError:
        return False


def crear_token(usuario_id: str, rol: str, empresa_id: str) -> str:
    payload = {
        "sub": usuario_id,
        "actor_id": usuario_id,
        "rol": rol,
        "empresa_id": empresa_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRACION_MIN),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verificar_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise AuthError("Token expirado")
    except jwt.InvalidTokenError:
        raise AuthError("Token inválido")
