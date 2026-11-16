# -*- coding: utf-8 -*-
"""Tests de cuentas anuales oficiales."""
from datetime import date

import psycopg
import pytest

from conta_rizoma4.cuentas_anuales_oficiales import (
    BalanceOficial, formatear_balance,
    PyGOficial, formatear_pyg,
    ECPN, formatear_ecpn,
    EFE, formatear_efe,
    Memoria, formatear_memoria,
)
from conta_rizoma4.custodia.repositorios import PG_URL


class TestBalance:
    def test_balance_cuadra(self):
        b = BalanceOficial()
        b.inmovilizado_material = 100_000
        b.efectivo = 50_000
        b.capital = 100_000
        b.reservas = 50_000
        assert b.total_activo == 150_000
        assert b.total_patrimonio_neto_y_pasivo == 150_000
        assert b.cuadra

    def test_formatear_desde_cuentas(self):
        activo = {2: {"217": 100_000}, 5: {"572": 50_000}}
        pasivo = {1: {"100": 100_000, "113": 50_000}}
        b = formatear_balance(activo, pasivo, 0)
        assert b.inmovilizado_material == 100_000
        assert b.efectivo == 50_000
        assert b.capital == 100_000
        assert b.reservas == 50_000
        assert b.cuadra


class TestPyG:
    def test_formatear(self):
        gastos = {"640": 200_000, "642": 60_000, "621": 10_000}
        ingresos = {"705": 500_000, "74": 10_000}
        p = formatear_pyg({}, gastos, ingresos)
        assert p.prestacion_servicios == 500_000
        assert p.sueldos_y_salarios == 200_000
        assert p.cargas_sociales == 60_000
        assert p.arrendamientos == 10_000
        assert p.otros_ingresos == 10_000
        assert p.resultado_explotacion == 240_000

    def test_resultado_negativo(self):
        gastos = {"640": 200_000}
        ingresos = {"705": 100_000}
        p = formatear_pyg({}, gastos, ingresos)
        assert p.resultado_explotacion == -100_000


class TestECPN:
    def test_saldo_final(self):
        e = formatear_ecpn(
            resultado_ejercicio=50_000,
            saldo_inicial_pn=100_000,
            variaciones_pn=[{"concepto": "Dividendos", "importe": -10_000}],
        )
        assert e.saldo_final == 140_000  # 100 + 50 - 10


class TestEFE:
    def test_flujo_explotacion(self):
        e = formatear_efe(
            resultado_antes_impuestos=100_000,
            amortizacion=10_000,
            variacion_capital_corriente=-5_000,
            impuestos_pagados=20_000,
        )
        # 100 + 10 - 5 - 20 = 85
        assert e.flujo_explotacion == 85_000

    def test_aumento_efectivo(self):
        e = formatear_efe(
            resultado_antes_impuestos=100_000,
            amortizacion=10_000,
            variacion_capital_corriente=0,
            impuestos_pagados=20_000,
            cobros_aportaciones=50_000,
        )
        assert e.aumento_efectivo > 0


class TestMemoria:
    def test_formatear(self):
        m = formatear_memoria(
            actividad="Construcción",
            resultado_ejercicio=50_000,
            capital=100_000,
            reservas=20_000,
        )
        assert m.actividad == "Construcción"
        assert m.patrimonio_neto["capital"] == 100_000
        assert m.propuesta_aplicacion_resultados["a_reservas"] == 50_000
