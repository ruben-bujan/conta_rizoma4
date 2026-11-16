# -*- coding: utf-8 -*-
"""Tests de modelos 200 y 303."""
import pytest

from conta_rizoma4.modelos_aeat import (
    Modelo200, calcular_modelo_200,
    Modelo303, calcular_modelo_303, calcular_desde_libros,
)


class TestModelo200:
    def test_sin_ajustes(self):
        m = calcular_modelo_200(resultado_contable=100_000_00)
        assert m.base_imponible == 100_000_00
        assert m.cuota_integra == 25_000_00  # 25%

    def test_con_ajustes(self):
        m = calcular_modelo_200(
            resultado_contable=100_000_00,
            ajustes_positivos=10_000_00,
            ajustes_negativos=5_000_00,
        )
        assert m.base_imponible == 105_000_00
        assert m.cuota_integra == 26_250_00

    def test_con_compensacion(self):
        m = calcular_modelo_200(
            resultado_contable=100_000_00,
            compensacion_bases_negativas=20_000_00,
        )
        assert m.base_imponible == 80_000_00
        assert m.cuota_integra == 20_000_00

    def test_con_retenciones(self):
        m = calcular_modelo_200(
            resultado_contable=100_000_00,
            retenciones=5_000_00,
            pagos_fraccionados=10_000_00,
        )
        assert m.cuota_diferencial == 10_000_00  # 25.000 - 5.000 - 10.000

    def test_perdida(self):
        m = calcular_modelo_200(resultado_contable=-50_000_00)
        assert m.base_imponible == 0
        assert m.cuota_integra == 0


class TestModelo303:
    def test_a_ingresar(self):
        m = calcular_modelo_303(
            iva_repercutido_base=100_000_00,
            iva_repercutido_cuota=21_000_00,
            iva_soportado_base=50_000_00,
            iva_soportado_cuota=10_500_00,
        )
        assert m.diferencia == 10_500_00
        assert m.resultado == 1  # a ingresar
        assert m.a_ingresar == 10_500_00

    def test_a_devolver(self):
        m = calcular_modelo_303(
            iva_repercutido_base=50_000_00,
            iva_repercutido_cuota=10_500_00,
            iva_soportado_base=100_000_00,
            iva_soportado_cuota=21_000_00,
        )
        assert m.diferencia == -10_500_00
        assert m.resultado == 2  # a devolver

    def test_con_compensacion(self):
        m = calcular_modelo_303(
            iva_repercutido_base=100_000_00,
            iva_repercutido_cuota=21_000_00,
            iva_soportado_base=50_000_00,
            iva_soportado_cuota=10_500_00,
            compensacion_anterior=5_000_00,
        )
        assert m.diferencia == 10_500_00
        assert m.a_ingresar == 5_500_00  # 10.500 - 5.000

    def test_desde_libros(self):
        lineas = [
            {"cuenta": "477", "debe_centimos": 0, "haber_centimos": 21_000_00},
            {"cuenta": "472", "debe_centimos": 10_500_00, "haber_centimos": 0},
        ]
        m = calcular_desde_libros(lineas)
        assert m.diferencia == 10_500_00
        assert m.resultado == 1
