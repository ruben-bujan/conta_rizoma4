# -*- coding: utf-8 -*-
"""Golden tests: 7 actos de facturación avanzada."""
from datetime import date

import pytest

from conta_rizoma4.actos.facturacion_avanzada import (
    ACTOS, crear_acto_fact_avanzada,
    fact_emit_simplificada, autofactura, fact_emit_con_descuento,
    fact_emit_rappel, fact_emit_recargo_equivalencia,
    aplicar_anticipo_cliente, fact_emit_con_recargo_demora,
)


GENESIS = "0" * 64
FECHA = date(2025, 6, 15)


def _lineas(acto):
    return [
        {"cuenta": l.cuenta_pgc, "debe": l.debe_centimos, "haber": l.haber_centimos}
        for l in acto.lineas
    ]


class TestSimplificada:
    def test_basica(self):
        a = fact_emit_simplificada(
            indice=0, hash_previo=GENESIS, fecha=FECHA,
            base_centimos=100_000, iva_pct=21,
            cliente_nif="B1", concepto="Ticket",
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "430", "debe": 121_000, "haber": 0} in d
        assert {"cuenta": "705", "debe": 0, "haber": 100_000} in d
        assert {"cuenta": "477", "debe": 0, "haber": 21_000} in d


class TestAutofactura:
    def test_basica(self):
        a = autofactura(
            indice=1, hash_previo=GENESIS, fecha=FECHA,
            base_centimos=100_000, iva_pct=21,
            proveedor_nif="B2", concepto="Autofactura",
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "629", "debe": 100_000, "haber": 0} in d
        assert {"cuenta": "472", "debe": 21_000, "haber": 0} in d
        assert {"cuenta": "400", "debe": 0, "haber": 121_000} in d


class TestDescuento:
    def test_basico(self):
        a = fact_emit_con_descuento(
            indice=2, hash_previo=GENESIS, fecha=FECHA,
            base_centimos=100_000, descuento_pct=10, iva_pct=21,
            cliente_nif="B3", concepto="Con descuento",
        )
        assert a.cuadra
        d = _lineas(a)
        # base 1000, desc 100, base neta 900, IVA 189, total 1089
        assert {"cuenta": "430", "debe": 108_900, "haber": 0} in d
        assert {"cuenta": "705", "debe": 0, "haber": 100_000} in d
        assert {"cuenta": "709", "debe": 10_000, "haber": 0} in d
        assert {"cuenta": "477", "debe": 0, "haber": 18_900} in d


class TestRappel:
    def test_basico(self):
        a = fact_emit_rappel(
            indice=3, hash_previo=GENESIS, fecha=FECHA,
            base_centimos=100_000, rappel_pct=5, iva_pct=21,
            cliente_nif="B4", concepto="Rappel",
        )
        assert a.cuadra
        d = _lineas(a)
        # rappel 50, IVA 10.5, total 60.5
        assert {"cuenta": "709", "debe": 5_000, "haber": 0} in d
        assert {"cuenta": "477", "debe": 1_050, "haber": 0} in d
        assert {"cuenta": "430", "debe": 0, "haber": 6_050} in d


class TestRecargoEquivalencia:
    def test_basico(self):
        a = fact_emit_recargo_equivalencia(
            indice=4, hash_previo=GENESIS, fecha=FECHA,
            base_centimos=100_000, iva_pct=21, recargo_pct=5.2,
            cliente_nif="B5", concepto="Recargo",
        )
        assert a.cuadra
        d = _lineas(a)
        # base 1000, IVA 210, recargo 52, total 1262
        assert {"cuenta": "430", "debe": 126_200, "haber": 0} in d
        assert {"cuenta": "705", "debe": 0, "haber": 100_000} in d
        assert {"cuenta": "477", "debe": 0, "haber": 21_000} in d
        assert {"cuenta": "478", "debe": 0, "haber": 5_200} in d


class TestAnticipo:
    def test_basico(self):
        a = aplicar_anticipo_cliente(
            indice=5, hash_previo=GENESIS, fecha=FECHA,
            base_centimos=100_000, iva_pct=21,
            cliente_nif="B6", concepto="Anticipo aplicado",
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "438", "debe": 121_000, "haber": 0} in d
        assert {"cuenta": "430", "debe": 0, "haber": 121_000} in d


class TestInteresesDemora:
    def test_basico(self):
        a = fact_emit_con_recargo_demora(
            indice=6, hash_previo=GENESIS, fecha=FECHA,
            base_centimos=100_000, recargo_pct=5,
            cliente_nif="B7", concepto="Intereses demora",
        )
        assert a.cuadra
        d = _lineas(a)
        # interés 50, IVA 10.5, total 60.5
        assert {"cuenta": "769", "debe": 0, "haber": 5_000} in d


class TestDispatcher:
    def test_codigo_invalido(self):
        with pytest.raises(ValueError, match="desconocido"):
            crear_acto_fact_avanzada("A_NO_EXISTE", indice=0, hash_previo=GENESIS)

    def test_cuenta_actos(self):
        assert len(ACTOS) == 7
