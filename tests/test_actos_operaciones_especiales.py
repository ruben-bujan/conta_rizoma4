# -*- coding: utf-8 -*-
"""Golden tests: 13 actos de operaciones especiales."""
from datetime import date

import pytest

from conta_rizoma4.actos.operaciones_especiales import (
    ACTOS, crear_acto_especial,
    fusion_por_absorcion, escision_parcial, fondo_de_comercio,
    eliminacion_intragrupo, atribucion_socios_minoritarios,
    compra_derivado, valoracion_derivado_favorable,
    valoracion_derivado_desfavorable,
    confirming_proveedor, factoring_cliente, descuento_efectos,
    pago_basado_acciones, venta_a_empresa_grupo,
)


GENESIS = "0" * 64
FECHA = date(2025, 6, 1)


def _lineas(acto):
    return [
        {"cuenta": l.cuenta_pgc, "debe": l.debe_centimos, "haber": l.haber_centimos}
        for l in acto.lineas
    ]


class TestCombinaciones:
    def test_fusion(self):
        a = fusion_por_absorcion(
            indice=0, hash_previo=GENESIS, fecha=FECHA,
            valor_razonable_centimos=1_000_000,
            capital_emitido_centimos=500_000,
            prima_centimos=100_000,
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "100", "debe": 0, "haber": 500_000} in d
        assert {"cuenta": "110", "debe": 0, "haber": 100_000} in d
        assert {"cuenta": "553", "debe": 0, "haber": 400_000} in d

    def test_escsion(self):
        a = escision_parcial(
            indice=1, hash_previo=GENESIS, fecha=FECHA,
            valor_escindido_centimos=300_000, cuenta_inmov="217",
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "553", "debe": 300_000, "haber": 0} in d
        assert {"cuenta": "217", "debe": 0, "haber": 300_000} in d

    def test_fondo_comercio(self):
        a = fondo_de_comercio(
            indice=2, hash_previo=GENESIS, fecha=FECHA, importe_centimos=200_000,
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "204", "debe": 200_000, "haber": 0} in d
        assert {"cuenta": "553", "debe": 0, "haber": 200_000} in d


class TestConsolidacion:
    def test_eliminacion(self):
        a = eliminacion_intragrupo(
            indice=3, hash_previo=GENESIS, fecha=FECHA,
            importe_centimos=50_000,
            cuenta_origen="430", cuenta_destino="400",
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "400", "debe": 50_000, "haber": 0} in d
        assert {"cuenta": "430", "debe": 0, "haber": 50_000} in d

    def test_atribucion_minoritarios(self):
        a = atribucion_socios_minoritarios(
            indice=4, hash_previo=GENESIS, fecha=FECHA, importe_centimos=100_000,
        )
        assert a.cuadra


class TestDerivados:
    def test_compra(self):
        a = compra_derivado(
            indice=5, hash_previo=GENESIS, fecha=FECHA, prima_centimos=10_000,
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "5590", "debe": 10_000, "haber": 0} in d
        assert {"cuenta": "572", "debe": 0, "haber": 10_000} in d

    def test_favorable(self):
        a = valoracion_derivado_favorable(
            indice=6, hash_previo=GENESIS, fecha=FECHA, importe_centimos=5_000,
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "7632", "debe": 0, "haber": 5_000} in d

    def test_desfavorable(self):
        a = valoracion_derivado_desfavorable(
            indice=7, hash_previo=GENESIS, fecha=FECHA, importe_centimos=3_000,
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "6632", "debe": 3_000, "haber": 0} in d


class TestFinanciacion:
    def test_confirming(self):
        a = confirming_proveedor(
            indice=8, hash_previo=GENESIS, fecha=FECHA, importe_centimos=100_000,
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "400", "debe": 100_000, "haber": 0} in d
        assert {"cuenta": "5208", "debe": 0, "haber": 100_000} in d

    def test_factoring(self):
        # Crédito 500.000, comisión 10.000. Neto 490.000.
        a = factoring_cliente(
            indice=9, hash_previo=GENESIS, fecha=FECHA,
            importe_centimos=500_000, comision_centimos=10_000,
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "572", "debe": 490_000, "haber": 0} in d
        assert {"cuenta": "626", "debe": 10_000, "haber": 0} in d
        assert {"cuenta": "430", "debe": 0, "haber": 500_000} in d

    def test_descuento(self):
        # Nominal 100.000, intereses 2.000. Neto 98.000.
        a = descuento_efectos(
            indice=10, hash_previo=GENESIS, fecha=FECHA,
            nominal_centimos=100_000, intereses_centimos=2_000,
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "572", "debe": 98_000, "haber": 0} in d
        assert {"cuenta": "626", "debe": 2_000, "haber": 0} in d
        assert {"cuenta": "431", "debe": 0, "haber": 100_000} in d


class TestPagosAcciones:
    def test_basico(self):
        a = pago_basado_acciones(
            indice=11, hash_previo=GENESIS, fecha=FECHA, importe_centimos=15_000,
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "640", "debe": 15_000, "haber": 0} in d
        assert {"cuenta": "111", "debe": 0, "haber": 15_000} in d


class TestVentaGrupo:
    def test_basico(self):
        a = venta_a_empresa_grupo(
            indice=12, hash_previo=GENESIS, fecha=FECHA,
            base_centimos=100_000, iva_pct=21,
            empresa_nif="B99999999",
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "430", "debe": 121_000, "haber": 0} in d
        assert {"cuenta": "705", "debe": 0, "haber": 100_000} in d
        assert {"cuenta": "477", "debe": 0, "haber": 21_000} in d


class TestDispatcher:
    def test_cuenta_actos(self):
        assert len(ACTOS) == 13

    def test_codigo_invalido(self):
        with pytest.raises(ValueError, match="desconocido"):
            crear_acto_especial("A_NO_EXISTE", indice=0, hash_previo=GENESIS)
