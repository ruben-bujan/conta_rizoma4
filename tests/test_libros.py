# -*- coding: utf-8 -*-
"""Tests de libro diario, mayor, balance de comprobación y cuentas anuales.

Usa un caso sintético: factura emitida (1000+21% IVA) + gasto (500+21% IVA)
+ cobro parcial. Verifica:
  - Diario: asientos ordenados
  - Mayor: saldos por cuenta
  - Balance comprobación: total debe = total haber
  - Balance situación: activo = pasivo + PN + resultado
  - PyG: ingresos - gastos = resultado
"""
from datetime import date

import pytest

from conta_rizoma4.partida_doble import (
    Linea, crear_asiento, guardar_asiento, borrar_asiento,
    RepositorioAsiento,
    listar_diario, totales_diario,
    mayor, balance_comprobacion,
    balance_situacion, cuenta_pyg,
)
from conta_rizoma4.actos.facturacion import (
    fact_emit_serv_nac_sin_ret, fact_rec_gasto_nac, cobro_cliente_transf,
)


GENESIS = "0" * 64
FECHA = date(2025, 4, 15)


@pytest.fixture
def caso_limpio():
    """Crea un caso sintético de 3 asientos y limpia al final."""
    repo = RepositorioAsiento()
    # Limpiar cualquier residuo
    for i in (8000, 8001, 8002):
        borrar_asiento(i)
    # Datos
    a0 = fact_emit_serv_nac_sin_ret(
        indice=8000, hash_previo=GENESIS, fecha=FECHA,
        base_centimos=100_000, iva_pct=21,
        cliente_nif="B12345678", concepto="Factura F-001",
    )
    a1 = fact_rec_gasto_nac(
        indice=8001, hash_previo=a0.hash, fecha=date(2025, 4, 16),
        base_centimos=50_000, iva_pct=21,
        cuenta_gasto="629", proveedor_nif="B87654321",
        concepto="Factura gasto G-001",
    )
    a2 = cobro_cliente_transf(
        indice=8002, hash_previo=a1.hash, fecha=date(2025, 4, 20),
        importe_centimos=121_000, cliente_nif="B12345678",
        concepto="Cobro F-001",
    )
    for a in (a0, a1, a2):
        guardar_asiento(a)
    yield repo
    for i in (8000, 8001, 8002):
        borrar_asiento(i)


class TestLibroDiario:
    def test_listar_diario(self, caso_limpio):
        asientos = listar_diario(caso_limpio, desde=8000, hasta=8002)
        assert len(asientos) == 3
        # Ordenados por índice
        assert [a["indice"] for a in asientos] == [8000, 8001, 8002]

    def test_totales_cuadran(self, caso_limpio):
        asientos = listar_diario(caso_limpio, desde=8000, hasta=8002)
        t = totales_diario(asientos)
        assert t["n_asientos"] == 3
        assert t["cuadra"]


class TestLibroMayor:
    def test_mayor_saldos(self, caso_limpio):
        m = mayor(caso_limpio, desde=8000, hasta=8002)
        # 430: D 121000 (factura), H 121000 (cobro) → saldo 0
        assert "430" in m
        assert m["430"]["debe"] == 121_000
        assert m["430"]["haber"] == 121_000
        assert m["430"]["saldo"] == 0
        # 705: H 100000 (ingreso) → saldo -100000 (acreedor)
        assert m["705"]["haber"] == 100_000
        assert m["705"]["saldo"] == -100_000
        # 477 (IVA repercutido): solo la factura emitida → H 21000
        assert m["477"]["haber"] == 21_000
        assert m["477"]["debe"] == 0
        # 472 (IVA soportado): solo la factura recibida → D 10500
        assert m["472"]["debe"] == 10_500
        assert m["472"]["haber"] == 0
        # 572 (banco): solo el cobro → D 121000
        assert m["572"]["debe"] == 121_000
        assert m["572"]["haber"] == 0
        assert m["572"]["saldo"] == 121_000

    def test_mayor_contiene_movimientos(self, caso_limpio):
        m = mayor(caso_limpio, desde=8000, hasta=8002)
        # 430: factura emitida (D) + cobro (H) → 2 movimientos
        assert len(m["430"]["movimientos"]) == 2
        # 572: solo el cobro → 1 movimiento
        assert len(m["572"]["movimientos"]) == 1
        # 705: solo la factura emitida → 1 movimiento
        assert len(m["705"]["movimientos"]) == 1


class TestBalanceComprobacion:
    def test_cuadra_global(self, caso_limpio):
        b = balance_comprobacion(caso_limpio, desde=8000, hasta=8002)
        assert b["cuadra"]
        assert b["total_debe"] == b["total_haber"]


class TestCuentasAnuales:
    def test_pyg_resultado(self, caso_limpio):
        p = cuenta_pyg(caso_limpio, desde=8000, hasta=8002)
        # Ingreso 705: 1000. Gasto 629: 500. Resultado: +500
        assert p["total_ingresos"] == 100_000
        assert p["total_gastos"] == 50_000
        assert p["resultado"] == 50_000  # beneficio 500 EUR
        assert "705" in p["ingresos"]
        assert "629" in p["gastos"]

    def test_balance_situacion_cuadra(self, caso_limpio):
        b = balance_situacion(caso_limpio, desde=8000, hasta=8002)
        # Activo: 572 (60.500) = 60500
        # Pasivo: 400 acreedor 60.500 → -60500, no... vamos a ver
        # 400: H 60500 (proveedor, acreedor) → saldo -60500 → pasivo 60500
        # 472: D 10500 → activo (HP deudora) → 10500
        # 477: H 31500 → pasivo (HP acreedora) → 31500
        # Resultado: 50000 (beneficio)
        # Activo = 60500 + 10500 = 71000
        # Pasivo + Resultado = 60500 + 31500 + 50000 = 142000
        # NO cuadra con estos números.
        # Hmm, algo falta. Repasemos.
        #
        # Asientos:
        # 1) Fact emit: D 430 121000 / H 705 100000, H 477 21000
        # 2) Fact rec: D 629 50000, D 472 10500 / H 400 60500
        # 3) Cobro: D 572 121000 / H 430 121000
        #
        # Saldos:
        # 430: D 121000 - H 121000 = 0
        # 705: H 100000 → saldo -100000 (ingreso)
        # 477: H 21000 → saldo -21000 (pasivo)
        # 629: D 50000 → saldo +50000 (gasto)
        # 472: D 10500 → saldo +10500 (activo)
        # 400: H 60500 → saldo -60500 (pasivo)
        # 572: D 121000 → saldo +121000 (activo)
        #
        # Activo: 472 (10500) + 572 (121000) = 131500
        # Pasivo: 400 (60500) + 477 (21000) = 81500
        # Resultado: ingresos 100000 - gastos 50000 = +50000
        # Total pasivo+resultado: 81500 + 50000 = 131500 ✅
        #
        # O sea que el balance SÍ cuadra. Corrijo mis cálculos.
        assert b["cuadra"], f"Activo={b['total_activo']} Pasivo+R={b['total_pasivo_mas_resultado']}"
        assert b["total_activo"] == 131_500
        assert b["resultado_ejercicio"] == 50_000
