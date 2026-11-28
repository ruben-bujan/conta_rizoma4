# -*- coding: utf-8 -*-
"""Backdating: la fecha contable retroactiva no debe romper la cadena."""
from datetime import date

import psycopg
import pytest

from conta_rizoma4.partida_doble import (
    RepositorioAsiento, crear_asiento, guardar_asiento, listar_diario, Linea,
)
from conta_rizoma4.partida_doble.persistencia import PG_URL
from conta_rizoma4.operativo.asiento import GENESIS

EMPRESA = "TEST_BACKDATING"


def _limpiar():
    with psycopg.connect(PG_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM linea_asiento WHERE empresa_id = %s", (EMPRESA,))
            cur.execute("DELETE FROM asiento_contable WHERE empresa_id = %s", (EMPRESA,))
        conn.commit()


@pytest.fixture
def limpio():
    _limpiar()
    yield
    _limpiar()


def _asiento(indice, fecha, hash_previo, concepto):
    return crear_asiento(
        indice=indice, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("572", debe_centimos=100_000),
            Linea("100", haber_centimos=100_000),
        ],
        hash_previo=hash_previo,
    )


def _cargar_con_backdating():
    # índice 0: marzo, registrado primero
    a0 = _asiento(0, date(2025, 3, 15), GENESIS, "A")
    guardar_asiento(a0, empresa_id=EMPRESA)
    # índice 1: enero, registrado después → backdating
    a1 = _asiento(1, date(2025, 1, 10), a0.hash, "B")
    guardar_asiento(a1, empresa_id=EMPRESA)


class TestBackdating:
    def test_fecha_retroactiva_no_rompe_la_cadena(self, limpio):
        _cargar_con_backdating()
        rep = RepositorioAsiento(EMPRESA).verificar_cadena()
        assert rep.total == 2
        assert rep.cadena_valida, f"Roturas: {rep.roturas}"

    def test_diario_sigue_ordenado_por_fecha(self, limpio):
        _cargar_con_backdating()
        diario = listar_diario(RepositorioAsiento(EMPRESA))
        assert [a["indice"] for a in diario] == [1, 0]  # enero antes que marzo

    def test_tampering_se_sigue_detectando(self, limpio):
        _cargar_con_backdating()
        with psycopg.connect(PG_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE asiento_contable SET concepto = %s "
                    "WHERE empresa_id = %s AND indice = %s",
                    ("Manipulado", EMPRESA, 1),
                )
            conn.commit()
        rep = RepositorioAsiento(EMPRESA).verificar_cadena()
        assert not rep.cadena_valida
        assert any(r["tipo"] == "hash_no_coincide" for r in rep.roturas)