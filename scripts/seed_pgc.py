#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Seed del PGC en Postgres para conta-rizoma4.

Lee de MariaDB (Contabilidad) y escribe en Postgres (conta_rizoma4).
Tres tablas:
  - pgc_cuenta: 906 cuentas (id, grupo, cuenta, descripcion)
  - pgc_texto: 3251 párrafos del texto legal del PGC
  - pgc_jerarquia: Nivel1..Nivel9 (jerarquía de 9 niveles)

Uso:
    export MARIADB_PASSWORD='...'
    export CONTA_PG_URL='postgresql://rizoma:rizoma_dev@localhost:5433/conta_rizoma4'
    python scripts/seed_pgc.py
"""
from __future__ import annotations

import os
import sys

import pymysql
import psycopg


MARIADB_CONFIG = {
    "host": os.environ.get("MARIADB_HOST", "localhost"),
    "port": int(os.environ.get("MARIADB_PORT", "3306")),
    "user": os.environ.get("MARIADB_USER", "root"),
    "password": os.environ.get("MARIADB_PASSWORD", ""),
    "database": os.environ.get("MARIADB_DB", "Contabilidad"),
}

PG_URL = os.environ.get(
    "CONTA_PG_URL",
    "postgresql://rizoma:rizoma_dev@localhost:5433/conta_rizoma4",
)


DDL = """
CREATE TABLE IF NOT EXISTS pgc_cuenta (
    id INTEGER PRIMARY KEY,
    grupo INTEGER NOT NULL,
    cuenta VARCHAR(20) NOT NULL,
    descripcion TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pgc_texto (
    id INTEGER PRIMARY KEY,
    jerarquia VARCHAR(50),
    n_pg INTEGER,
    n_linea INTEGER,
    texto TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pgc_jerarquia (
    nivel VARCHAR(20) NOT NULL,
    id INTEGER NOT NULL,
    codigo VARCHAR(20) NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    PRIMARY KEY (nivel, id)
);

CREATE INDEX IF NOT EXISTS idx_pgc_cuenta_cuenta ON pgc_cuenta(cuenta);
CREATE INDEX IF NOT EXISTS idx_pgc_texto_jerarquia ON pgc_texto(jerarquia);
CREATE INDEX IF NOT EXISTS idx_pgc_jerarquia_nivel ON pgc_jerarquia(nivel);
"""


def _seed_cuentas(src_cur, dst_cur) -> int:
    """906 cuentas del PGC."""
    src_cur.execute("SELECT Id, grupo, cuenta, descripcion FROM PGC")
    rows = src_cur.fetchall()
    if not rows:
        print("  [aviso] PGC vacío")
        return 0
    dst_cur.executemany(
        "INSERT INTO pgc_cuenta (id, grupo, cuenta, descripcion) "
        "VALUES (%s, %s, %s, %s) "
        "ON CONFLICT (id) DO NOTHING",
        rows,
    )
    return len(rows)


def _seed_texto(src_cur, dst_cur) -> int:
    """3251 párrafos del texto legal del PGC."""
    src_cur.execute(
        "SELECT id, Jerarquia, N_pg, N_linea, Texto FROM NuevaTabla_3"
    )
    rows = src_cur.fetchall()
    if not rows:
        print("  [aviso] NuevaTabla_3 vacía")
        return 0
    dst_cur.executemany(
        "INSERT INTO pgc_texto (id, jerarquia, n_pg, n_linea, texto) "
        "VALUES (%s, %s, %s, %s, %s) "
        "ON CONFLICT (id) DO NOTHING",
        rows,
    )
    return len(rows)


def _seed_jerarquia(src_cur, dst_cur) -> dict[str, int]:
    """Nivel1..Nivel9. Detecta columnas dinámicamente (id/new_id, cuenta/codigo, descripcion/nombre)."""
    resultado = {}
    for nivel in range(1, 10):
        tabla = f"Nivel{nivel}"

        # 1. ¿Existe la tabla?
        try:
            src_cur.execute(f"SHOW COLUMNS FROM {tabla}")
            columnas = {row[0].lower() for row in src_cur.fetchall()}
        except pymysql.err.ProgrammingError:
            resultado[tabla] = -1
            continue

        # 2. Detectar columna de ID (id o new_id)
        col_id = next(
            (c for c in ("id", "new_id", "id_nivel", "nivel_id") if c in columnas),
            None,
        )
        if col_id is None:
            resultado[tabla] = -1
            print(f"  {tabla}: sin columna ID, omitido")
            continue

        # 3. Detectar columnas de código y nombre
        col_codigo = next(
            (c for c in ("cuenta", "codigo", "codigo_cuenta") if c in columnas),
            None,
        )
        col_nombre = next(
            (c for c in ("descripcion", "nombre", "desc") if c in columnas),
            None,
        )
        if col_codigo is None or col_nombre is None:
            resultado[tabla] = -1
            print(f"  {tabla}: columnas faltantes (código={col_codigo}, nombre={col_nombre})")
            continue

        # 4. Extraer
        src_cur.execute(f"SELECT {col_id}, {col_codigo}, {col_nombre} FROM {tabla}")
        rows = src_cur.fetchall()
        if not rows:
            resultado[tabla] = 0
            continue

        # 5. Insertar en Postgres
        dst_cur.executemany(
            "INSERT INTO pgc_jerarquia (nivel, id, codigo, nombre) "
            "VALUES (%s, %s, %s, %s) "
            "ON CONFLICT (nivel, id) DO NOTHING",
            [(f"nivel{nivel}", r[0], r[1], r[2]) for r in rows],
        )
        resultado[tabla] = len(rows)
    return resultado


def main() -> int:
    if not MARIADB_CONFIG["password"]:
        print("ERROR: falta MARIADB_PASSWORD", file=sys.stderr)
        return 1

    print(f"MariaDB:  {MARIADB_CONFIG['user']}@{MARIADB_CONFIG['host']}:"
          f"{MARIADB_CONFIG['port']}/{MARIADB_CONFIG['database']}")
    print(f"Postgres: {PG_URL}")

    src = pymysql.connect(**MARIADB_CONFIG)
    src_cur = src.cursor()

    try:
        with psycopg.connect(PG_URL) as dst:
            with dst.cursor() as dst_cur:
                dst_cur.execute(DDL)
                print("DDL OK")

                n = _seed_cuentas(src_cur, dst_cur)
                print(f"pgc_cuenta: {n} filas")

                n = _seed_texto(src_cur, dst_cur)
                print(f"pgc_texto: {n} filas")

                jer = _seed_jerarquia(src_cur, dst_cur)
                for tabla, n in jer.items():
                    if n == -1:
                        print(f"  {tabla}: no existe (omitido)")
                    elif n == 0:
                        print(f"  {tabla}: 0 filas")
                    else:
                        print(f"  {tabla}: {n} filas")

                dst.commit()
                print("Seed completado")
    finally:
        src_cur.close()
        src.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())