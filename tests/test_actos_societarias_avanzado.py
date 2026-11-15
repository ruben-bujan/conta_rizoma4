# -*- coding: utf-8 -*-
"""Golden tests: 7 actos de societarias avanzado."""
from datetime import date

import pytest

from conta_rizoma4.actos.societarias_avanzado import (
    ACTOS, crear_acto_societario_avanzado,
    adquisicion_autocartera, venta_autocartera,
    dividendo_a_cuenta, aplicacion_resultado,
    prima_emision, reserva_voluntaria, transformacion_sociedad,
)


GENESIS = "0" * 64
FECHA = date(2025, 6, 30)


def _lineas(acto):
    return [
        {"cuenta": l.cuenta_pgc, "debe": l.debe_centimos, "haber": l.haber_centimos}
        for l in acto.lineas
    ]


class TestAutocartera:
    def test_adquisicion(self):
        a = adquisicion_autocartera(
            indice=0, hash_previo=GENESIS, fecha=FECHA, importe_centimos=100_000,
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "108", "debe": 100_000, "haber": 0} in d
        assert {"cuenta": "572", "debe": 0, "haber": 100_000} in d

    def test_venta_con_beneficio(self):
        # Compra 100.000, venta 120.000. Beneficio 20.000.
        a = venta_autocartera(
            indice=1, hash_previo=GENESIS, fecha=FECHA,
            precio_centimos=120_000, coste_centimos=100_000,
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "572", "debe": 120_000, "haber": 0} in d
        assert {"cuenta": "108", "debe": 0, "haber": 100_000} in d
        assert {"cuenta": "1136", "debe": 0, "haber": 20_000} in d


class TestDividendoACuenta:
    def test_basico(self):
        # Dividendo 100.000, retención 19%
        a = dividendo_a_cuenta(
            indice=2, hash_previo=GENESIS, fecha=FECHA,
            importe_centimos=100_000, retencion_pct=19,
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "129", "debe": 100_000, "haber": 0} in d
        assert {"cuenta": "526", "debe": 0, "haber": 81_000} in d
        assert {"cuenta": "4751", "debe": 0, "haber": 19_000} in d


class TestAplicacionResultado:
    def test_beneficio(self):
        # Beneficio 100.000. Reserva legal 10.000. Voluntaria 20.000. Resto 70.000.
        a = aplicacion_resultado(
            indice=3, hash_previo=GENESIS, fecha=FECHA,
            resultado_centimos=100_000,
            reserva_legal_centimos=10_000,
            reservas_voluntarias_centimos=20_000,
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "129", "debe": 100_000, "haber": 0} in d
        assert {"cuenta": "112", "debe": 0, "haber": 10_000} in d
        assert {"cuenta": "113", "debe": 0, "haber": 20_000} in d
        assert {"cuenta": "121", "debe": 0, "haber": 70_000} in d

    def test_perdida(self):
        a = aplicacion_resultado(
            indice=4, hash_previo=GENESIS, fecha=FECHA,
            resultado_centimos=-50_000,
            reserva_legal_centimos=0,
            reservas_voluntarias_centimos=0,
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "121", "debe": 50_000, "haber": 0} in d
        assert {"cuenta": "129", "debe": 0, "haber": 50_000} in d


class TestPrimaEmision:
    def test_basico(self):
        a = prima_emision(
            indice=5, hash_previo=GENESIS, fecha=FECHA, importe_centimos=200_000,
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "572", "debe": 200_000, "haber": 0} in d
        assert {"cuenta": "110", "debe": 0, "haber": 200_000} in d


class TestReservaVoluntaria:
    def test_basico(self):
        a = reserva_voluntaria(
            indice=6, hash_previo=GENESIS, fecha=FECHA, importe_centimos=50_000,
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "129", "debe": 50_000, "haber": 0} in d
        assert {"cuenta": "113", "debe": 0, "haber": 50_000} in d


class TestTransformacion:
    def test_basico(self):
        a = transformacion_sociedad(
            indice=7, hash_previo=GENESIS, fecha=FECHA, importe_centimos=300_000,
        )
        assert a.cuadra


class TestDispatcher:
    def test_cuenta_actos(self):
        assert len(ACTOS) == 7

    def test_codigo_invalido(self):
        with pytest.raises(ValueError, match="desconocido"):
            crear_acto_societario_avanzado("A_NO_EXISTE", indice=0, hash_previo=GENESIS)
