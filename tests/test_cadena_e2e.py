# -*- coding: utf-8 -*-
"""Verificación end-to-end de la cadena de actos económicos.

Crea 3 actos encadenados, los persiste, y verifica:
  - El primero tiene hash_previo = GENESIS.
  - Cada uno tiene hash_previo = hash del anterior.
  - Los 3 hashes son distintos.
  - Los 3 están en Postgres.
"""
from __future__ import annotations

from datetime import date

import psycopg

from conta_rizoma4.operativo.asiento import GENESIS
from conta_rizoma4.operativo.acto_economico import (
    crear_acto_economico,
    guardar_acto_economico,
)
from conta_rizoma4.operativo.acto_economico import PG_URL


class TestCadenaE2E:
    def test_tres_actos_encadenados_y_persistidos(self):
        # 1. Limpiar los 3 índices del test (idempotente)
        with psycopg.connect(PG_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM acto_economico WHERE indice BETWEEN 9100 AND 9102"
                )
            conn.commit()

        # 2. Crear 3 actos encadenados
        a0 = crear_acto_economico(
            indice=9100, fecha=date(2025, 1, 1),
            cuenta_pgc="705", importe_centimos=121_000,
            concepto="Factura 2025-001", creado_por="rubén",
            hash_previo=GENESIS,
        )
        a1 = crear_acto_economico(
            indice=9101, fecha=date(2025, 2, 1),
            cuenta_pgc="705", importe_centimos=242_000,
            concepto="Factura 2025-002", creado_por="rubén",
            hash_previo=a0.hash,
        )
        a2 = crear_acto_economico(
            indice=9102, fecha=date(2025, 3, 1),
            cuenta_pgc="705", importe_centimos=363_000,
            concepto="Factura 2025-003", creado_por="rubén",
            hash_previo=a1.hash,
        )

        # 3. Verificar la cadena en memoria
        assert a0.hash_previo == GENESIS
        assert a1.hash_previo == a0.hash
        assert a2.hash_previo == a1.hash
        assert len({a0.hash, a1.hash, a2.hash}) == 3  # los 3 distintos

        # 4. Persistir
        for a in (a0, a1, a2):
            guardar_acto_economico(a)

        # 5. Verificar en Postgres
        with psycopg.connect(PG_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT indice, hash, hash_previo FROM acto_economico "
                    "WHERE indice BETWEEN 9100 AND 9102 ORDER BY indice"
                )
                filas = cur.fetchall()

        assert len(filas) == 3
        idxs = [f[0] for f in filas]
        hashes = [f[1] for f in filas]
        previos = [f[2] for f in filas]

        assert idxs == [9100, 9101, 9102]
        assert previos[0] == GENESIS
        assert previos[1] == hashes[0]
        assert previos[2] == hashes[1]