# -*- coding: utf-8 -*-
"""Golden tests: 6 actos de inmovilizado avanzado."""
from datetime import date

import pytest

from conta_rizoma4.actos.inmovilizado_avanzado import (
    ACTOS, crear_acto_inmov_avanzado,
    leasing_financiero_inicio, leasing_financiero_cuota,
    permuta_inmovilizado, reclasificar_activo_para_venta,
    deterioro_reversible_inmov, actualizacion_valor_inmov,
)


GENESIS = "0" * 64
FECHA = date(2025, 6, 15)


def _lineas(acto):
    return [
        {"cuenta": l.cuenta_pgc, "debe": l.debe_centimos, "haber": l.haber_centimos}
        for l in acto.lineas
    ]


class TestLeasingInicio:
    def test_basico(self):
        a = leasing_financiero_inicio(
            indice=0, hash_previo=GENESIS, fecha=FECHA,
            valor_razonable_centimos=1_200_000,
            cuota_largo_plazo_centimos=800_000,
            cuota_corto_plazo_centimos=400_000,
            cuenta_inmov="218", proveedor_nif="B1",
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "218", "debe": 1_200_000, "haber": 0} in d
        assert {"cuenta": "174", "debe": 0, "haber": 800_000} in d
        assert {"cuenta": "524", "debe": 0, "haber": 400_000} in d

    def test_descuadre_lp_cp_falla(self):
        with pytest.raises(ValueError, match="descuadre leasing"):
            leasing_financiero_inicio(
                indice=0, hash_previo=GENESIS, fecha=FECHA,
                valor_razonable_centimos=1_200_000,
                cuota_largo_plazo_centimos=800_000,
                cuota_corto_plazo_centimos=300_000,  # 1.100.000 != 1.200.000
                cuenta_inmov="218", proveedor_nif="B1",
            )


class TestLeasingCuota:
    def test_basico(self):
        # Cuota 100.000, 20.000 de intereses, IVA 21%
        a = leasing_financiero_cuota(
            indice=1, hash_previo=GENESIS, fecha=FECHA,
            cuota_centimos=100_000, interes_centimos=20_000,
            iva_pct=21,
        )
        assert a.cuadra
        d = _lineas(a)
        # amortización = 100.000 - 20.000 = 80.000
        assert {"cuenta": "524", "debe": 80_000, "haber": 0} in d
        assert {"cuenta": "662", "debe": 20_000, "haber": 0} in d
        # IVA sobre 100.000 = 21.000
        assert {"cuenta": "472", "debe": 21_000, "haber": 0} in d
        assert {"cuenta": "572", "debe": 0, "haber": 121_000} in d


class TestPermuta:
    def test_con_beneficio(self):
        # Entregado: VNC 100.000. Recibido: 150.000. Beneficio: 50.000.
        a = permuta_inmovilizado(
            indice=2, hash_previo=GENESIS, fecha=FECHA,
            valor_razonable_recibido_centimos=150_000,
            valor_neto_contable_entregado_centimos=100_000,
            cuenta_inmov_entregado="217",
            cuenta_inmov_recibido="218",
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "218", "debe": 150_000, "haber": 0} in d
        assert {"cuenta": "217", "debe": 0, "haber": 100_000} in d
        assert {"cuenta": "771", "debe": 0, "haber": 50_000} in d


class TestReclasificar:
    def test_basico(self):
        a = reclasificar_activo_para_venta(
            indice=3, hash_previo=GENESIS, fecha=FECHA,
            importe_centimos=500_000, cuenta_inmov_origen="217",
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "580", "debe": 500_000, "haber": 0} in d
        assert {"cuenta": "217", "debe": 0, "haber": 500_000} in d


class TestDeterioroReversible:
    def test_basico(self):
        a = deterioro_reversible_inmov(
            indice=4, hash_previo=GENESIS, fecha=FECHA,
            importe_centimos=10_000,
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "291", "debe": 10_000, "haber": 0} in d
        assert {"cuenta": "791", "debe": 0, "haber": 10_000} in d


class TestActualizacionValor:
    def test_basico(self):
        a = actualizacion_valor_inmov(
            indice=5, hash_previo=GENESIS, fecha=FECHA,
            importe_centimos=50_000, cuenta_inmov="217",
        )
        assert a.cuadra
        d = _lineas(a)
        assert {"cuenta": "217", "debe": 50_000, "haber": 0} in d
        assert {"cuenta": "134", "debe": 0, "haber": 50_000} in d


class TestDispatcher:
    def test_cuenta_actos(self):
        assert len(ACTOS) == 6

    def test_codigo_invalido(self):
        with pytest.raises(ValueError, match="desconocido"):
            crear_acto_inmov_avanzado("A_NO_EXISTE", indice=0, hash_previo=GENESIS)
