# -*- coding: utf-8 -*-
"""Golden tests de los 23 actos del Ciclo 10 (inmovilizado, existencias,
societarias, ajustes)."""
from datetime import date

import pytest

from conta_rizoma4.actos.inmovilizado import (
    ACTOS as A_INMOV, crear_acto_inmov,
    compra_inmov_material, venta_inmovilizado,
    amortizacion_anual, deterioro_inmovilizado, baja_inmovilizado,
)
from conta_rizoma4.actos.existencias import (
    ACTOS as A_EXIST, crear_acto_existencias,
    compra_existencias, venta_existencias,
    regularizacion_existencias, deterioro_existencias,
)
from conta_rizoma4.actos.societarias import (
    ACTOS as A_SOC, crear_acto_societario,
    constitucion_sociedad, ampliacion_capital, dividendo_pagado,
    reserva_legal, reduccion_capital,
)
from conta_rizoma4.actos.ajustes import (
    ACTOS as A_AJUSTE, crear_acto_ajuste,
    subvencion_capital_cobro, subvencion_capital_imputacion,
    subvencion_explotacion, periodificacion_gasto_anticipado,
    periodificacion_ingreso_anticipado, dif_cambio_positiva,
    dif_cambio_negativa, provision_garantia, provision_litigio,
)


GENESIS = "0" * 64
FECHA = date(2025, 6, 15)


def _lineas(acto):
    return [
        {"cuenta": l.cuenta_pgc, "debe": l.debe_centimos, "haber": l.haber_centimos}
        for l in acto.lineas
    ]


class TestInmovilizado:
    def test_compra_1000_21(self):
        a = compra_inmov_material(
            indice=0, hash_previo=GENESIS, fecha=FECHA,
            base_centimos=100_000, iva_pct=21,
            cuenta_inmov="217", proveedor_nif="B11111111", concepto="Ordenador",
        )
        assert a.cuadra
        assert a.total_debe == a.total_haber == 121_000
        d = _lineas(a)
        assert {"cuenta": "217", "debe": 100_000, "haber": 0} in d
        assert {"cuenta": "472", "debe": 21_000, "haber": 0} in d
        assert {"cuenta": "400", "debe": 0, "haber": 121_000} in d

    def test_venta_con_beneficio(self):
        # Precio 1500, valor neto contable 1000, amort acum 500, coste 1500, IVA 21%
        a = venta_inmovilizado(
            indice=1, hash_previo=GENESIS, fecha=FECHA,
            precio_centimos=150_000, iva_pct=21,
            cuenta_inmov="217", amort_acumulada_centimos=50_000,
            valor_neto_contable_centimos=100_000,
            cliente_nif="B22222222", concepto="Venta ordenador",
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "430", "debe": 181_500, "haber": 0} in d
        assert {"cuenta": "28", "debe": 50_000, "haber": 0} in d
        assert {"cuenta": "771", "debe": 0, "haber": 50_000} in d
        assert {"cuenta": "477", "debe": 0, "haber": 31_500} in d

    def test_amortizacion(self):
        a = amortizacion_anual(
            indice=2, hash_previo=GENESIS, fecha=date(2025, 12, 31),
            importe_centimos=200_000, cuenta_gasto="681", cuenta_amort="281",
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "681", "debe": 200_000, "haber": 0} in d
        assert {"cuenta": "281", "debe": 0, "haber": 200_000} in d

    def test_deterioro(self):
        a = deterioro_inmovilizado(
            indice=3, hash_previo=GENESIS, fecha=FECHA,
            importe_centimos=100_000,
        )
        assert a.cuadra

    def test_baja(self):
        a = baja_inmovilizado(
            indice=4, hash_previo=GENESIS, fecha=FECHA,
            cuenta_inmov="217", amort_acumulada_centimos=800_000,
            valor_neto_contable_centimos=200_000,
        )
        assert a.cuadra


class TestExistencias:
    def test_compra(self):
        a = compra_existencias(
            indice=10, hash_previo=GENESIS, fecha=FECHA,
            base_centimos=500_000, iva_pct=21,
            cuenta_compra="600", proveedor_nif="B11111111", concepto="Compra",
        )
        assert a.cuadra

    def test_venta(self):
        a = venta_existencias(
            indice=11, hash_previo=GENESIS, fecha=FECHA,
            base_centimos=800_000, iva_pct=21,
            cliente_nif="B22222222", concepto="Venta",
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "700", "debe": 0, "haber": 800_000} in d

    def test_regularizacion_aumento(self):
        a = regularizacion_existencias(
            indice=12, hash_previo=GENESIS, fecha=date(2025, 12, 31),
            saldo_inicial_centimos=500_000, saldo_final_centimos=800_000,
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "300", "debe": 300_000, "haber": 0} in d
        assert {"cuenta": "610", "debe": 0, "haber": 300_000} in d

    def test_regularizacion_sin_variacion_falla(self):
        with pytest.raises(ValueError, match="sin variación"):
            regularizacion_existencias(
                indice=13, hash_previo=GENESIS, fecha=date(2025, 12, 31),
                saldo_inicial_centimos=500_000, saldo_final_centimos=500_000,
            )

    def test_deterioro(self):
        a = deterioro_existencias(
            indice=14, hash_previo=GENESIS, fecha=FECHA,
            importe_centimos=50_000,
        )
        assert a.cuadra


class TestSocietarias:
    def test_constitucion(self):
        a = constitucion_sociedad(
            indice=20, hash_previo=GENESIS, fecha=FECHA,
            capital_centimos=3_000_000,
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "572", "debe": 3_000_000, "haber": 0} in d
        assert {"cuenta": "100", "debe": 0, "haber": 3_000_000} in d

    def test_ampliacion(self):
        a = ampliacion_capital(
            indice=21, hash_previo=GENESIS, fecha=FECHA,
            capital_centimos=1_000_000, prima_centimos=200_000,
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "110", "debe": 0, "haber": 200_000} in d

    def test_dividendo(self):
        a = dividendo_pagado(
            indice=22, hash_previo=GENESIS, fecha=FECHA,
            dividendo_centimos=1_000_000, retencion_pct=19,
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "4751", "debe": 0, "haber": 190_000} in d
        assert {"cuenta": "572", "debe": 0, "haber": 810_000} in d

    def test_reserva_legal(self):
        a = reserva_legal(
            indice=23, hash_previo=GENESIS, fecha=FECHA,
            importe_centimos=300_000,
        )
        assert a.cuadra

    def test_reduccion_capital(self):
        a = reduccion_capital(
            indice=24, hash_previo=GENESIS, fecha=FECHA,
            importe_centimos=500_000,
        )
        assert a.cuadra


class TestAjustes:
    def test_subvencion_capital_cobro(self):
        a = subvencion_capital_cobro(
            indice=30, hash_previo=GENESIS, fecha=FECHA,
            importe_centimos=1_000_000,
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "130", "debe": 0, "haber": 1_000_000} in d

    def test_subvencion_capital_imputacion(self):
        a = subvencion_capital_imputacion(
            indice=31, hash_previo=GENESIS, fecha=date(2025, 12, 31),
            importe_centimos=100_000,
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "746", "debe": 0, "haber": 100_000} in d

    def test_subvencion_explotacion(self):
        a = subvencion_explotacion(
            indice=32, hash_previo=GENESIS, fecha=FECHA,
            importe_centimos=200_000,
        )
        assert a.cuadra

    def test_periodificacion_gasto(self):
        a = periodificacion_gasto_anticipado(
            indice=33, hash_previo=GENESIS, fecha=date(2025, 12, 31),
            importe_centimos=50_000, cuenta_gasto="629",
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "480", "debe": 50_000, "haber": 0} in d
        assert {"cuenta": "629", "debe": 0, "haber": 50_000} in d

    def test_periodificacion_ingreso(self):
        a = periodificacion_ingreso_anticipado(
            indice=34, hash_previo=GENESIS, fecha=date(2025, 12, 31),
            importe_centimos=80_000, cuenta_ingreso="705",
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "485", "debe": 0, "haber": 80_000} in d

    def test_dif_cambio_positiva(self):
        a = dif_cambio_positiva(
            indice=35, hash_previo=GENESIS, fecha=FECHA,
            importe_centimos=15_000,
        )
        assert a.cuadra

    def test_dif_cambio_negativa(self):
        a = dif_cambio_negativa(
            indice=36, hash_previo=GENESIS, fecha=FECHA,
            importe_centimos=15_000,
        )
        assert a.cuadra

    def test_provision_garantia(self):
        a = provision_garantia(
            indice=37, hash_previo=GENESIS, fecha=date(2025, 12, 31),
            importe_centimos=100_000,
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "143", "debe": 0, "haber": 100_000} in d

    def test_provision_litigio(self):
        a = provision_litigio(
            indice=38, hash_previo=GENESIS, fecha=date(2025, 12, 31),
            importe_centimos=200_000,
        )
        assert a.cuadra


class TestDispatchers:
    def test_inmov(self):
        assert len(A_INMOV) == 5
        a = crear_acto_inmov(
            "A_COMPRA_INMOV_MATERIAL",
            indice=40, hash_previo=GENESIS, fecha=FECHA,
            base_centimos=100_000, iva_pct=21,
            cuenta_inmov="217", proveedor_nif="X", concepto="X",
        )
        assert a.cuadra

    def test_existencias(self):
        assert len(A_EXIST) == 4

    def test_societarias(self):
        assert len(A_SOC) == 5

    def test_ajustes(self):
        assert len(A_AJUSTE) == 9

    def test_codigo_invalido(self):
        with pytest.raises(ValueError):
            crear_acto_inmov("A_NO_EXISTE", indice=0, hash_previo=GENESIS)
        with pytest.raises(ValueError):
            crear_acto_societario("A_NO_EXISTE", indice=0, hash_previo=GENESIS)
        with pytest.raises(ValueError):
            crear_acto_ajuste("A_NO_EXISTE", indice=0, hash_previo=GENESIS)
