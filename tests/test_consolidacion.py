# -*- coding: utf-8 -*-
"""Tests de consolidación de grupo clásico."""
from datetime import date

import psycopg
import pytest

from conta_rizoma4.partida_doble import (
    RepositorioAsiento, crear_asiento, guardar_asiento, Linea,
    borrar_asiento,
)
from conta_rizoma4.partida_doble.persistencia import PG_URL
from conta_rizoma4.operativo.asiento import GENESIS
from conta_rizoma4.consolidacion import (
    RelacionGrupo, cargar_relaciones, guardar_relacion, consolidar_grupo,
    ConsolidacionError,
)


MATRIZ = "TEST_MATRIZ"
FILIAL_A = "TEST_FILIAL_A"
FILIAL_B = "TEST_FILIAL_B"


def _limpiar():
    with psycopg.connect(PG_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM relaciones_grupo "
                "WHERE matriz_id = %s OR filial_id IN (%s, %s)",
                (MATRIZ, FILIAL_A, FILIAL_B),
            )
            for emp in (MATRIZ, FILIAL_A, FILIAL_B):
                cur.execute(
                    "DELETE FROM linea_asiento WHERE empresa_id = %s", (emp,)
                )
                cur.execute(
                    "DELETE FROM asiento_contable WHERE empresa_id = %s", (emp,)
                )
        conn.commit()


@pytest.fixture
def grupo_limpio():
    _limpiar()
    yield
    _limpiar()


class TestRelaciones:
    def test_crear_relacion(self, grupo_limpio):
        rel = RelacionGrupo(
            matriz_id=MATRIZ, filial_id=FILIAL_A,
            porcentaje=80.0, fecha_inicio=date(2025, 1, 1),
        )
        guardar_relacion(rel)
        relaciones = cargar_relaciones(MATRIZ, date(2025, 6, 1))
        assert len(relaciones) == 1
        assert relaciones[0].filial_id == FILIAL_A
        assert relaciones[0].porcentaje == 80.0

    def test_porcentaje_invalido_falla(self):
        with pytest.raises(ConsolidacionError, match="porcentaje"):
            RelacionGrupo(
                matriz_id=MATRIZ, filial_id=FILIAL_A,
                porcentaje=0, fecha_inicio=date(2025, 1, 1),
            )


class TestConsolidacion:
    def test_grupo_simple(self, grupo_limpio):
        # Matriz: 100% A, 80% B
        guardar_relacion(RelacionGrupo(
            matriz_id=MATRIZ, filial_id=FILIAL_A,
            porcentaje=100.0, fecha_inicio=date(2025, 1, 1),
        ))
        guardar_relacion(RelacionGrupo(
            matriz_id=MATRIZ, filial_id=FILIAL_B,
            porcentaje=80.0, fecha_inicio=date(2025, 1, 1),
        ))

        # Asientos: cada empresa con 1.000 capital + 1.000 banco
        for emp in (MATRIZ, FILIAL_A, FILIAL_B):
            a = crear_asiento(
                indice=0, fecha=date(2025, 1, 1), concepto=f"Aporte {emp}",
                lineas=[
                    Linea("572", debe_centimos=100_000),
                    Linea("100", haber_centimos=100_000),
                ],
                hash_previo=GENESIS,
            )
            guardar_asiento(a, empresa_id=emp)

        cons = consolidar_grupo("JV_VECTOR", MATRIZ, date(2025, 6, 1))
        assert len(cons.empresas_incluidas) == 3
        assert cons.resultado_grupo == 0  # sin ingresos/gastos
        assert cons.cuadra
