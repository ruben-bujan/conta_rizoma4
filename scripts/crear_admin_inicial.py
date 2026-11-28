#!/usr/bin/env python3
"""Crea un administrador inicial desde consola local, una sola vez.

El endpoint público no admite autoalta ni elevación a admin. Ejecuta este
bootstrap con acceso administrativo a PostgreSQL durante el despliegue inicial.
"""
from __future__ import annotations

import argparse
from getpass import getpass
import sys
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from conta_rizoma4.auth import hash_password
from conta_rizoma4.config import get_empresa
from conta_rizoma4.config.postgresql import PG_URL


def crear_admin(*, usuario_id: str, email: str, nombre: str, empresa_id: str, password: str) -> None:
    if not all(x.strip() for x in (usuario_id, email, nombre, empresa_id)):
        raise ValueError("usuario_id, email, nombre y empresa_id son obligatorios")
    if len(password) < 12:
        raise ValueError("La contraseña debe tener al menos 12 caracteres")
    get_empresa(empresa_id)
    with psycopg.connect(PG_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT pg_advisory_xact_lock(741522, 1)")
            cur.execute("SELECT COUNT(*) FROM usuarios WHERE rol = 'admin'")
            if cur.fetchone()[0]:
                raise RuntimeError("Ya existe un administrador; bootstrap rechazado")
            cur.execute(
                "INSERT INTO usuarios (usuario_id,email,password_hash,nombre,rol,empresa_id) "
                "VALUES (%s,%s,%s,%s,'admin',%s)",
                (usuario_id, email, hash_password(password), nombre, empresa_id),
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usuario-id", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--nombre", required=True)
    parser.add_argument("--empresa-id", required=True)
    parser.add_argument("--confirmar", action="store_true")
    args = parser.parse_args()
    if not args.confirmar:
        parser.error("Añade --confirmar para crear el primer administrador")
    password = getpass("Contraseña (mínimo 12 caracteres): ")
    confirmar_password = getpass("Repite la contraseña: ")
    if password != confirmar_password:
        parser.error("Las contraseñas no coinciden")
    crear_admin(
        usuario_id=args.usuario_id, email=args.email, nombre=args.nombre,
        empresa_id=args.empresa_id, password=password,
    )
    print("Administrador inicial creado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
