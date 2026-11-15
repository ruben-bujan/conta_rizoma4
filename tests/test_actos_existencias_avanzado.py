# -*- coding: utf-8 -*-
"""Golden tests: 3 actos de existencias avanzado."""
from datetime import date

import pytest

from conta_rizoma4.actos.existencias_avanzado import (
    ACTOS, crear_acto_existencias_avanzado,
    correccion_valorativa_existencias,
    deterioro_reversible_existencias,
    regularizacion_existencias_fifo,
)


GENESIS = "0" * 64
FECHA = date(2025, 12, 31)


def _lineas(acto):
    return [
        {"cuenta": l.cuenta_pgc, "debe": l.debe_centimos, "haber": l.haber_centimos}
        for l in acto.lineas
    ]


class TestCorreccion:
    def test_basico(self):
        a = correccion_valorativa_existencias(
            indice=0, hash_previo=GENESIS, fecha=FECHA, importe_centimos=30_000,
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "693", "debe": 30_000, "haber": 0} in d
        assert {"cuenta": "390", "debe": 0, "haber": 30_000} in d


class TestDeterioroReversible:
    def test_basico(self):
        a = deterioro_reversible_existencias(
            indice=1, hash_previo=GENESIS, fecha=FECHA, importe_centimos=15_000,
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "390", "debe": 15_000, "haber": 0} in d
        assert {"cuenta": "793", "debe": 0, "haber": 15_000} in d


class TestFIFO:
    def test_aumento(self):
        a = regularizacion_existencias_fifo(
            indice=2, hash_previo=GENESIS, fecha=FECHA,
            saldo_inicial_centimos=100_000, saldo_final_fifo_centimos=120_000,
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "300", "debe": 20_000, "haber": 0} in d
        assert {"cuenta": "610", "debe": 0, "haber": 20_000} in d

    def test_disminucion(self):
        a = regularizacion_existencias_fifo(
            indice=3, hash_previo=GENESIS, fecha=FECHA,
            saldo_inicial_centimos=120_000, saldo_final_fifo_centimos=100_000,
        )
        assert a.cuadra

    def test_sin_variacion_falla(self):
        with pytest.raises(ValueError, match="sin variación"):
            regularizacion_existencias_fifo(
                indice=4, hash_previo=GENESIS, fecha=FECHA,
                saldo_inicial_centimos=100_000, saldo_final_fifo_centimos=100_000,
            )


class TestDispatcher:
    def test_cuenta_actos(self):
        assert len(ACTOS) == 3

    def test_codigo_invalido(self):
        with pytest.raises(ValueError, match="desconocido"):
            crear_acto_existencias_avanzado("A_NO_EXISTE", indice=0, hash_previo=GENESIS)
