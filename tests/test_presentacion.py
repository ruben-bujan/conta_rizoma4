# -*- coding: utf-8 -*-
"""Tests de presentacion.py (balance y PyG agrupados por PGC)."""
from datetime import date

import pytest

from conta_rizoma4.partida_doble import (
    guardar_asiento,
    balance_formateado, pyg_formateado, RepositorioAsiento,
)
from conta_rizoma4.actos.facturacion import (
    fact_emit_serv_nac_sin_ret, fact_rec_gasto_nac,
)
from conta_rizoma4.actos.inmovilizado import amortizacion_anual
from conta_rizoma4.actos.facturacion import fact_rec_inmov
from conta_rizoma4.operativo.asiento import GENESIS
from test_helpers_db import limpiar_asiento_prueba


@pytest.fixture
def caso_simple():
    """Caso: 2 facturas, 1 gasto, 1 compra inmovilizado, 1 amortización."""
    for i in (8900, 8901, 8902, 8903, 8904):
        limpiar_asiento_prueba(i)
    a0 = fact_emit_serv_nac_sin_ret(
        indice=8900, hash_previo=GENESIS, fecha=date(2025, 1, 15),
        base_centimos=100_000, iva_pct=21,
        cliente_nif="B1", concepto="Factura 1",
    )
    guardar_asiento(a0)
    a1 = fact_rec_gasto_nac(
        indice=8901, hash_previo=a0.hash, fecha=date(2025, 1, 20),
        base_centimos=50_000, iva_pct=21, cuenta_gasto="600",
        proveedor_nif="B2", concepto="Compra",
    )
    guardar_asiento(a1)
    a2 = fact_rec_inmov(
        indice=8902, hash_previo=a1.hash, fecha=date(2025, 2, 1),
        base_centimos=120_000, iva_pct=21, cuenta_inmov="217",
        proveedor_nif="B3", concepto="Inmovilizado",
    )
    guardar_asiento(a2)
    a3 = amortizacion_anual(
        indice=8903, hash_previo=a2.hash, fecha=date(2025, 3, 31),
        importe_centimos=7_500, cuenta_gasto="681", cuenta_amort="281",
    )
    guardar_asiento(a3)
    yield
    for i in (8900, 8901, 8902, 8903, 8904):
        limpiar_asiento_prueba(i)


class TestBalanceFormateado:
    def test_activo_y_pasivo(self, caso_simple):
        b = balance_formateado(RepositorioAsiento('default'), desde=8900, hasta=8903)
        # Activo grupo 2: 217=120k, 281=-7.5k (corrector)
        # Activo grupo 4: 430=121k, 472=25.2k+10.5k=35.7k
        # Activo grupo 5: 572=0 (no hay cobro)
        # Pasivo grupo 1: 400=121k (de la factura gasto)
        # Pasivo grupo 4: 400=145.2k (inmovilizado) + 477=21k
        assert b["activo"][2]["217"] == 120_000
        assert b["correctores"]["281"] == 7_500
        assert b["cuadra"]

    def test_cuadra(self, caso_simple):
        b = balance_formateado(RepositorioAsiento('default'), desde=8900, hasta=8903)
        assert b["cuadra"], (
            f"Activo={b['total_activo']} "
            f"Pasivo+R={b['total_pasivo_mas_resultado']}"
        )


class TestPyGFormateado:
    def test_separa_gastos_e_ingresos(self, caso_simple):
        p = pyg_formateado(RepositorioAsiento('default'), desde=8900, hasta=8903)
        # Ingresos: 705=100k
        assert "705" in p["ingresos"]
        # Gastos: 600=50k, 681=7.5k
        assert "600" in p["gastos"]
        assert "681" in p["gastos"]

    def test_resultado(self, caso_simple):
        p = pyg_formateado(RepositorioAsiento('default'), desde=8900, hasta=8903)
        # 100k - 57.5k = 42.5k
        assert p["resultado"] == 42_500
