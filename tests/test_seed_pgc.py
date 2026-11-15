# -*- coding: utf-8 -*-
"""Verificación del seed del PGC en Postgres."""
from __future__ import annotations

import os

import psycopg
import pytest


PG_URL = os.environ.get(
    "CONTA_PG_URL",
    "postgresql://rizoma:rizoma_dev@localhost:5433/conta_rizoma4",
)


@pytest.fixture(scope="module")
def conn():
    try:
        c = psycopg.connect(PG_URL, connect_timeout=2)
    except Exception as e:
        pytest.skip(f"Postgres no disponible: {e}")
    yield c
    c.close()


class TestSeedPGC:
    def test_cuentas_cargadas(self, conn):
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM pgc_cuenta")
            n = cur.fetchone()[0]
        assert n == 906, f"Esperadas 906 cuentas, hay {n}"

    def test_texto_cargado(self, conn):
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM pgc_texto")
            n = cur.fetchone()[0]
        assert n >= 3000, f"Esperados >=3000 párrafos, hay {n}"

    def test_jerarquia_cargada(self, conn):
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM pgc_jerarquia")
            n = cur.fetchone()[0]
        assert n >= 900, f"Esperadas >=900 filas jerarquía, hay {n}"

    def test_cuenta_capital(self, conn):
        with conn.cursor() as cur:
            cur.execute("SELECT descripcion FROM pgc_cuenta WHERE cuenta = '10'")
            row = cur.fetchone()
        assert row is not None
        assert "CAPITAL" in row[0].upper()

    def test_primer_parrafo_legal(self, conn):
        with conn.cursor() as cur:
            cur.execute("SELECT texto FROM pgc_texto WHERE id = 1")
            row = cur.fetchone()
        assert row is not None
        assert "MARCO CONCEPTUAL" in row[0].upper()