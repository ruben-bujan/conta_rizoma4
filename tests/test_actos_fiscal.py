# -*- coding: utf-8 -*-
"""Golden tests de los actos fiscales + cierre."""
from datetime import date

import pytest

from conta_rizoma4.actos.fiscal import (
    ACTOS as ACTOS_FISCAL, crear_acto_fiscal,
    liq_iva_trim_303_ingresar, liq_iva_trim_303_devolver,
    liq_iva_trim_303_compensar, resumen_anual_iva_390,
    liq_irpf_trim_111, liq_irpf_trim_115, liq_irpf_trim_123,
    resumen_anual_190, resumen_anual_180, resumen_anual_193,
    liq_is_anual_200,
)
from conta_rizoma4.actos.cierre import (
    ACTOS as ACTOS_CIERRE, crear_acto_cierre,
    regularizacion_grupos_6_7, cierre_ejercicio, apertura_ejercicio,
)

GENESIS = "0" * 64
FECHA = date(2025, 3, 31)


def _lineas(acto):
    return [
        {"cuenta": l.cuenta_pgc, "debe": l.debe_centimos, "haber": l.haber_centimos}
        for l in acto.lineas
    ]


class TestIVALiquidaciones:
    def test_ingresar(self):
        a = liq_iva_trim_303_ingresar(
            indice=0, hash_previo=GENESIS, fecha=FECHA,
            iva_repercutido_centimos=210_000,
            iva_soportado_centimos=150_000, concepto="IVA T1",
        )
        assert a.cuadra
        assert a.total_debe == a.total_haber == 210_000
        d = _lineas(a)
        assert {"cuenta": "477", "debe": 210_000, "haber": 0} in d
        assert {"cuenta": "472", "debe": 0, "haber": 150_000} in d
        assert {"cuenta": "4750", "debe": 0, "haber": 60_000} in d

    def test_devolver(self):
        a = liq_iva_trim_303_devolver(
            indice=1, hash_previo=GENESIS, fecha=FECHA,
            iva_repercutido_centimos=100_000,
            iva_soportado_centimos=180_000, concepto="IVA T1 dev",
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "4700", "debe": 80_000, "haber": 0} in d

    def test_compensar(self):
        a = liq_iva_trim_303_compensar(
            indice=2, hash_previo=GENESIS, fecha=FECHA,
            iva_repercutido_centimos=100_000,
            iva_soportado_centimos=150_000, concepto="IVA T1 comp",
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "4700", "debe": 50_000, "haber": 0} in d

    def test_ingresar_negativo_falla(self):
        with pytest.raises(ValueError, match="a ingresar debe ser > 0"):
            liq_iva_trim_303_ingresar(
                indice=0, hash_previo=GENESIS, fecha=FECHA,
                iva_repercutido_centimos=100_000,
                iva_soportado_centimos=150_000, concepto="X",
            )


class TestIVAResumen:
    def test_390_positivo(self):
        a = resumen_anual_iva_390(
            indice=3, hash_previo=GENESIS, fecha=date(2025, 12, 31),
            iva_repercutido_centimos=2_100_000,
            iva_soportado_centimos=1_500_000, concepto="390",
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "4750", "debe": 0, "haber": 600_000} in d

    def test_390_sin_diferencias_falla(self):
        with pytest.raises(ValueError, match="sin diferencias"):
            resumen_anual_iva_390(
                indice=3, hash_previo=GENESIS, fecha=date(2025, 12, 31),
                iva_repercutido_centimos=1_000_000,
                iva_soportado_centimos=1_000_000, concepto="X",
            )


class TestIRPF:
    def test_111(self):
        a = liq_irpf_trim_111(
            indice=4, hash_previo=GENESIS, fecha=FECHA,
            retenciones_centimos=45_000, concepto="111",
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "4751", "debe": 45_000, "haber": 0} in d
        assert {"cuenta": "572", "debe": 0, "haber": 45_000} in d

    def test_115(self):
        a = liq_irpf_trim_115(
            indice=5, hash_previo=GENESIS, fecha=FECHA,
            retenciones_centimos=19_000, concepto="115",
        )
        assert a.cuadra

    def test_123(self):
        a = liq_irpf_trim_123(
            indice=6, hash_previo=GENESIS, fecha=FECHA,
            retenciones_centimos=3_800, concepto="123",
        )
        assert a.cuadra

    def test_190(self):
        a = resumen_anual_190(
            indice=7, hash_previo=GENESIS, fecha=date(2025, 12, 31),
            retenciones_centimos=180_000, concepto="190",
        )
        assert a.cuadra

    def test_180(self):
        a = resumen_anual_180(
            indice=8, hash_previo=GENESIS, fecha=date(2025, 12, 31),
            retenciones_centimos=76_000, concepto="180",
        )
        assert a.cuadra

    def test_193(self):
        a = resumen_anual_193(
            indice=9, hash_previo=GENESIS, fecha=date(2025, 12, 31),
            retenciones_centimos=15_200, concepto="193",
        )
        assert a.cuadra


class TestIS:
    def test_200(self):
        a = liq_is_anual_200(
            indice=10, hash_previo=GENESIS, fecha=date(2025, 7, 25),
            base_imponible_centimos=4_000_000, tipo_pct=25, concepto="IS",
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "6300", "debe": 1_000_000, "haber": 0} in d
        assert {"cuenta": "4752", "debe": 0, "haber": 1_000_000} in d


class TestDispatcherFiscal:
    def test_crear_acto_fiscal(self):
        a = crear_acto_fiscal(
            "A_LIQ_IRPF_TRIM_111",
            indice=20, hash_previo=GENESIS, fecha=FECHA,
            retenciones_centimos=10_000, concepto="Test",
        )
        assert a.cuadra

    def test_codigo_invalido(self):
        with pytest.raises(ValueError, match="Acto fiscal desconocido"):
            crear_acto_fiscal("A_NO_EXISTE", indice=0, hash_previo=GENESIS)

    def test_cuenta_actos(self):
        assert len(ACTOS_FISCAL) == 11


class TestRegularizacion:
    def test_beneficio(self):
        a = regularizacion_grupos_6_7(
            indice=30, hash_previo=GENESIS, fecha=date(2025, 12, 31),
            saldos_grupo_6_7={"600": -500_000, "700": 800_000},
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "600", "debe": 0, "haber": 500_000} in d
        assert {"cuenta": "700", "debe": 800_000, "haber": 0} in d
        assert {"cuenta": "129", "debe": 0, "haber": 300_000} in d

    def test_perdida(self):
        a = regularizacion_grupos_6_7(
            indice=31, hash_previo=GENESIS, fecha=date(2025, 12, 31),
            saldos_grupo_6_7={"600": -800_000, "700": 500_000},
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "129", "debe": 300_000, "haber": 0} in d

    def test_sin_resultado_falla(self):
        with pytest.raises(ValueError, match="sin resultado"):
            regularizacion_grupos_6_7(
                indice=32, hash_previo=GENESIS, fecha=date(2025, 12, 31),
                saldos_grupo_6_7={"600": -100_000, "700": 100_000},
            )


class TestCierreApertura:
    def test_cierre(self):
        a = cierre_ejercicio(
            indice=40, hash_previo=GENESIS, fecha=date(2025, 12, 31),
            saldos_balance={"572": -1_000_000, "100": 1_000_000},
        )
        assert a.cuadra

    def test_cierre_descuadrado_falla(self):
        with pytest.raises(ValueError, match="descuadrado"):
            cierre_ejercicio(
                indice=41, hash_previo=GENESIS, fecha=date(2025, 12, 31),
                saldos_balance={"572": -1_000_000, "100": 500_000},
            )

    def test_apertura(self):
        a = apertura_ejercicio(
            indice=42, hash_previo=GENESIS, fecha=date(2026, 1, 1),
            saldos_balance={"572": -1_000_000, "100": 1_000_000},
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "572", "debe": 1_000_000, "haber": 0} in d
        assert {"cuenta": "100", "debe": 0, "haber": 1_000_000} in d


class TestDispatcherCierre:
    def test_cuenta_actos(self):
        assert len(ACTOS_CIERRE) == 3

    def test_crear_acto_cierre(self):
        a = crear_acto_cierre(
            "A_CIERRE_EJERCICIO",
            indice=50, hash_previo=GENESIS, fecha=date(2025, 12, 31),
            saldos_balance={"572": -1_000_000, "100": 1_000_000},
        )
        assert a.cuadra
