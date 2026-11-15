# -*- coding: utf-8 -*-
"""Golden tests: 5 actos de ajustes avanzado."""
from datetime import date

import pytest

from conta_rizoma4.actos.ajustes_avanzado import (
    ACTOS, crear_acto_ajuste_avanzado,
    provision_desmantelamiento, provision_medioambiental,
    cobertura_flujo_efectivo, correccion_error_ejercicio_anterior,
    cambio_criterio_contable,
)


GENESIS = "0" * 64
FECHA = date(2025, 12, 31)


def _lineas(acto):
    return [
        {"cuenta": l.cuenta_pgc, "debe": l.debe_centimos, "haber": l.haber_centimos}
        for l in acto.lineas
    ]


class TestDesmantelamiento:
    def test_basico(self):
        a = provision_desmantelamiento(
            indice=0, hash_previo=GENESIS, fecha=FECHA,
            importe_centimos=50_000, cuenta_inmov="211",
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "211", "debe": 50_000, "haber": 0} in d
        assert {"cuenta": "143", "debe": 0, "haber": 50_000} in d


class TestMedioambiental:
    def test_basico(self):
        a = provision_medioambiental(
            indice=1, hash_previo=GENESIS, fecha=FECHA, importe_centimos=30_000,
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "622", "debe": 30_000, "haber": 0} in d
        assert {"cuenta": "145", "debe": 0, "haber": 30_000} in d


class TestCobertura:
    def test_basico(self):
        a = cobertura_flujo_efectivo(
            indice=2, hash_previo=GENESIS, fecha=FECHA, importe_centimos=10_000,
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "910", "debe": 10_000, "haber": 0} in d
        assert {"cuenta": "133", "debe": 0, "haber": 10_000} in d


class TestCorreccionError:
    def test_basico(self):
        a = correccion_error_ejercicio_anterior(
            indice=3, hash_previo=GENESIS, fecha=FECHA,
            importe_centimos=5_000, cuenta_afectada="629",
        )
        assert a.cuadra


class TestCambioCriterio:
    def test_basico(self):
        a = cambio_criterio_contable(
            indice=4, hash_previo=GENESIS, fecha=FECHA,
            importe_centimos=8_000, cuenta_afectada="217",
        )
        assert a.cuadra


class TestDispatcher:
    def test_cuenta_actos(self):
        assert len(ACTOS) == 5

    def test_codigo_invalido(self):
        with pytest.raises(ValueError, match="desconocido"):
            crear_acto_ajuste_avanzado("A_NO_EXISTE", indice=0, hash_previo=GENESIS)
