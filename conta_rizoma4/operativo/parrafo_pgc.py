# -*- coding: utf-8 -*-
"""Búsqueda del párrafo del PGC que justifica una cuenta.

Dos pasos:
  1. Buscar por código de cuenta (p.ej. "705" en el texto).
  2. Fallback: buscar por descripción ("Prestación de servicios").

Devuelve dict con {id, jerarquia, n_pg, n_linea, texto} o None.
"""
from __future__ import annotations

import os
from typing import Optional

import psycopg


PG_URL = os.environ.get(
    "CONTA_PG_URL",
    "postgresql://rizoma:rizoma_dev@localhost:5433/conta_rizoma4",
)


def buscar_parrafo_pgc(
    cuenta: str,
    descripcion: str = "",
    pg_url: Optional[str] = None,
) -> Optional[dict]:
    """Primer párrafo del PGC que menciona la cuenta o su descripción."""
    url = pg_url or PG_URL
    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            # 1. Por código exacto (frontera de palabra)
            cur.execute(
                "SELECT id, jerarquia, n_pg, n_linea, texto FROM pgc_texto "
                "WHERE texto ~ %s "
                "ORDER BY n_pg ASC, n_linea ASC LIMIT 1",
                (rf"\m{cuenta}\M",),
            )
            row = cur.fetchone()
            if row:
                return _fila_a_dict(row)
            # 2. Fallback: por descripción
            if descripcion:
                cur.execute(
                    "SELECT id, jerarquia, n_pg, n_linea, texto FROM pgc_texto "
                    "WHERE texto ILIKE %s "
                    "ORDER BY n_pg ASC, n_linea ASC LIMIT 1",
                    (f"%{descripcion}%",),
                )
                row = cur.fetchone()
                if row:
                    return _fila_a_dict(row)
    return None


def buscar_parrafos_por_cuenta(
    cuenta: str,
    descripcion: str = "",
    limit: int = 3,
    pg_url: Optional[str] = None,
) -> list[dict]:
    """Hasta `limit` párrafos del PGC que mencionan la cuenta."""
    url = pg_url or PG_URL
    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, jerarquia, n_pg, n_linea, texto FROM pgc_texto "
                "WHERE texto ~ %s "
                "ORDER BY n_pg ASC, n_linea ASC LIMIT %s",
                (rf"\m{cuenta}\M", limit),
            )
            rows = cur.fetchall()
    return [_fila_a_dict(r) for r in rows]


def _fila_a_dict(row: tuple) -> dict:
    id_, jerarquia, n_pg, n_linea, texto = row
    return {
        "id": id_,
        "jerarquia": jerarquia,
        "n_pg": n_pg,
        "n_linea": n_linea,
        "texto": texto,
    }