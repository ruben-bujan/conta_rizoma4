# -*- coding: utf-8 -*-
"""Autenticación: JWT + Argon2id."""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Optional

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


JWT_SECRET = os.environ.get("CONTA_JWT_SECRET", "dev-secret-change-me")
JWT_ALGORITHM = "HS256"
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
        "rol": rol,
        "empresa_id": empresa_id,
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRACION_MIN),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verificar_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise AuthError("Token expirado")
    except jwt.InvalidTokenError:
        raise AuthError("Token inválido")
