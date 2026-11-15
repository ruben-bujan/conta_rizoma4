# -*- coding: utf-8 -*-
"""Golden tests: 23 actos fiscales avanzados."""
from datetime import date

import pytest

from conta_rizoma4.actos.fiscal_avanzado import (
    ACTOS, crear_acto_fiscal_avanzado,
    modelo_347, modelo_349, modelo_369,
    pago_fraccionado_130, pago_fraccionado_131,
    iae, ibi, itp_ajd,
    sancion_tributaria, interes_demora,
    regularizacion_iva, regularizacion_irpf, regularizacion_is,
    iva_foral, igic_canarias,
    modelo_720, modelo_721, modelo_714,
    impuesto_primas_seguros, impuesto_actividades_juego,
    impuesto_hidrocarburos, impuesto_alcohol, impuesto_tabaco,
)


GENESIS = "0" * 64
FECHA = date(2025, 6, 15)


def _lineas(acto):
    return [
        {"cuenta": l.cuenta_pgc, "debe": l.debe_centimos, "haber": l.haber_centimos}
        for l in acto.lineas
    ]


class TestInformativos:
    """Los 6 informativos: 555 con 1 céntimo en cada lado (autocancelado)."""
    def test_347(self):
        a = modelo_347(indice=0, hash_previo=GENESIS, fecha=FECHA)
        assert a.cuadra

    def test_349(self):
        a = modelo_349(indice=1, hash_previo=GENESIS, fecha=FECHA)
        assert a.cuadra

    def test_369(self):
        a = modelo_369(indice=2, hash_previo=GENESIS, fecha=FECHA)
        assert a.cuadra

    def test_720(self):
        a = modelo_720(indice=3, hash_previo=GENESIS, fecha=FECHA)
        assert a.cuadra

    def test_721(self):
        a = modelo_721(indice=4, hash_previo=GENESIS, fecha=FECHA)
        assert a.cuadra

    def test_714(self):
        a = modelo_714(indice=5, hash_previo=GENESIS, fecha=FECHA)
        assert a.cuadra


class TestPagosFraccionados:
    def test_130(self):
        a = pago_fraccionado_130(
            indice=10, hash_previo=GENESIS, fecha=FECHA,
            importe_centimos=50_000,
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "473", "debe": 50_000, "haber": 0} in d
        assert {"cuenta": "572", "debe": 0, "haber": 50_000} in d

    def test_131(self):
        a = pago_fraccionado_131(
            indice=11, hash_previo=GENESIS, fecha=FECHA,
            importe_centimos=30_000,
        )
        assert a.cuadra


class TestLocales:
    def test_iae(self):
        a = iae(indice=20, hash_previo=GENESIS, fecha=FECHA, importe_centimos=15_000)
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "631", "debe": 15_000, "haber": 0} in d

    def test_ibi(self):
        a = ibi(indice=21, hash_previo=GENESIS, fecha=FECHA, importe_centimos=20_000)
        assert a.cuadra

    def test_itp(self):
        a = itp_ajd(
            indice=22, hash_previo=GENESIS, fecha=FECHA,
            base_centimos=100_000, tipo_pct=10,
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "631", "debe": 10_000, "haber": 0} in d


class TestSanciones:
    def test_sancion(self):
        a = sancion_tributaria(
            indice=30, hash_previo=GENESIS, fecha=FECHA, importe_centimos=5_000,
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "678", "debe": 5_000, "haber": 0} in d
        assert {"cuenta": "4752", "debe": 0, "haber": 5_000} in d

    def test_interes_demora(self):
        a = interes_demora(
            indice=31, hash_previo=GENESIS, fecha=FECHA, importe_centimos=2_000,
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "669", "debe": 2_000, "haber": 0} in d


class TestRegularizaciones:
    def test_iva(self):
        a = regularizacion_iva(
            indice=40, hash_previo=GENESIS, fecha=FECHA, importe_centimos=10_000,
        )
        assert a.cuadra

    def test_irpf(self):
        a = regularizacion_irpf(
            indice=41, hash_previo=GENESIS, fecha=FECHA, importe_centimos=5_000,
        )
        assert a.cuadra

    def test_is(self):
        a = regularizacion_is(
            indice=42, hash_previo=GENESIS, fecha=FECHA, importe_centimos=20_000,
        )
        assert a.cuadra


class TestForales:
    def test_iva_foral(self):
        a = iva_foral(
            indice=50, hash_previo=GENESIS, fecha=FECHA,
            iva_repercutido_centimos=100_000,
            iva_soportado_centimos=80_000,
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "4750", "debe": 0, "haber": 20_000} in d

    def test_igic(self):
        a = igic_canarias(
            indice=51, hash_previo=GENESIS, fecha=FECHA,
            igic_repercutido_centimos=70_000,
            igic_soportado_centimos=50_000,
        )
        assert a.cuadra


class TestImpuestosEspeciales:
    def test_primas_seguros(self):
        a = impuesto_primas_seguros(
            indice=60, hash_previo=GENESIS, fecha=FECHA,
            base_centimos=100_000, tipo_pct=8,
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "625", "debe": 8_000, "haber": 0} in d
        assert {"cuenta": "4752", "debe": 0, "haber": 8_000} in d

    def test_juego(self):
        a = impuesto_actividades_juego(
            indice=61, hash_previo=GENESIS, fecha=FECHA, importe_centimos=10_000,
        )
        assert a.cuadra

    def test_hidrocarburos(self):
        a = impuesto_hidrocarburos(
            indice=62, hash_previo=GENESIS, fecha=FECHA, importe_centimos=5_000,
        )
        assert a.cuadra

    def test_alcohol(self):
        a = impuesto_alcohol(
            indice=63, hash_previo=GENESIS, fecha=FECHA, importe_centimos=3_000,
        )
        assert a.cuadra

    def test_tabaco(self):
        a = impuesto_tabaco(
            indice=64, hash_previo=GENESIS, fecha=FECHA, importe_centimos=4_000,
        )
        assert a.cuadra


class TestDispatcher:
    def test_cuenta_actos(self):
        assert len(ACTOS) == 23

    def test_codigo_invalido(self):
        with pytest.raises(ValueError, match="desconocido"):
            crear_acto_fiscal_avanzado("A_NO_EXISTE", indice=0, hash_previo=GENESIS)
