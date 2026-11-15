# -*- coding: utf-8 -*-
"""Persistencia de asientos y lineas en Postgres (multi-empresa)."""
from __future__ import annotations

import json
import os
from typing import Optional

import psycopg

from .modelo import Asiento


PG_URL = os.environ.get(
    "CONTA_PG_URL",
    "postgresql://rizoma:rizoma_dev@localhost:5433/conta_rizoma4",
)


def guardar_asiento(
    acto: Asiento,
    pg_url: Optional[str] = None,
    empresa_id: str = "default",
) -> None:
    """Inserta el asiento y sus lineas. Idempotente por (empresa_id, indice).

    empresa_id es obligatorio en la practica; el default 'default' permite
    que los tests antiguos (sin empresa) sigan funcionando.
    """
    if not empresa_id or not empresa_id.strip():
        raise ValueError("empresa_id no puede estar vacio")
    url = pg_url or PG_URL
    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO asiento_contable
                    (indice, fecha, concepto, hash_previo, hash, metadatos,
                     empresa_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (empresa_id, indice) DO NOTHING
                """,
                (
                    acto.indice, acto.fecha, acto.concepto,
                    acto.hash_previo, acto.hash, json.dumps(acto.metadatos),
                    empresa_id,
                ),
            )
            for l in acto.lineas:
                cur.execute(
                    """
                    INSERT INTO linea_asiento
                        (asiento_indice, cuenta_pgc, debe_centimos,
                         haber_centimos, parrafo_pgc_id, concepto_linea,
                         empresa_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        acto.indice, l.cuenta_pgc, l.debe_centimos,
                        l.haber_centimos, l.parrafo_pgc_id, l.concepto_linea,
                        empresa_id,
                    ),
                )
        conn.commit()


def borrar_asiento(
    indice: int,
    pg_url: Optional[str] = None,
    empresa_id: str = "default",
) -> None:
    url = pg_url or PG_URL
    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM linea_asiento "
                "WHERE empresa_id = %s AND asiento_indice = %s",
                (empresa_id, indice),
            )
            cur.execute(
                "DELETE FROM asiento_contable "
                "WHERE empresa_id = %s AND indice = %s",
                (empresa_id, indice),
            )
        conn.commit()
