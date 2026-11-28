"""Helpers de integración: crear usuarios de prueba sin exposición de signup."""
from __future__ import annotations

import psycopg

from conta_rizoma4.auth import hash_password
from conta_rizoma4.partida_doble.persistencia import PG_URL


def sembrar_usuario(*, usuario_id: str, email: str, password: str,
                    nombre: str, rol: str, empresa_id: str) -> None:
    with psycopg.connect(PG_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO usuarios (usuario_id,email,password_hash,nombre,rol,empresa_id,activo) "
                "VALUES (%s,%s,%s,%s,%s,%s,TRUE) "
                "ON CONFLICT (usuario_id) DO UPDATE SET email=EXCLUDED.email, "
                "password_hash=EXCLUDED.password_hash,nombre=EXCLUDED.nombre, "
                "rol=EXCLUDED.rol,empresa_id=EXCLUDED.empresa_id,activo=TRUE",
                (usuario_id, email, hash_password(password), nombre, rol, empresa_id),
            )
