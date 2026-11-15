# -*- coding: utf-8 -*-
"""Persistencia de asientos y líneas en Postgres."""
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


def guardar_asiento(acto: Asiento, pg_url: Optional[str] = None) -> None:
    url = pg_url or PG_URL
    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO asiento_contable
                    (indice, fecha, concepto, hash_previo, hash, metadatos)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (indice) DO NOTHING
                """,
                (
                    acto.indice, acto.fecha, acto.concepto,
                    acto.hash_previo, acto.hash, json.dumps(acto.metadatos),
                ),
            )
            for l in acto.lineas:
                cur.execute(
                    """
                    INSERT INTO linea_asiento
                        (asiento_indice, cuenta_pgc, debe_centimos,
                         haber_centimos, parrafo_pgc_id, concepto_linea)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        acto.indice, l.cuenta_pgc, l.debe_centimos,
                        l.haber_centimos, l.parrafo_pgc_id, l.concepto_linea,
                    ),
                )
        conn.commit()


def borrar_asiento(indice: int, pg_url: Optional[str] = None) -> None:
    url = pg_url or PG_URL
    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM linea_asiento WHERE asiento_indice = %s", (indice,)
            )
            cur.execute(
                "DELETE FROM asiento_contable WHERE indice = %s", (indice,)
            )
        conn.commit()
