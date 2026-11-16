# -*- coding: utf-8 -*-
"""Modelo 200 (Impuesto sobre Sociedades).

Basado en la Orden HFP/227/2017 (o la vigente).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Modelo200:
    """Liquidación del Impuesto sobre Sociedades."""
    # Resultado contable
    resultado_contable: int = 0

    # Ajustes extracontables
    ajustes_positivos: int = 0
    ajustes_negativos: int = 0

    # Base imponible
    base_imponible_previa: int = 0
    compensacion_bases_negativas: int = 0
    base_imponible: int = 0

    # Cuota íntegra
    tipo_impositivo: float = 25.0  # %
    cuota_integra: int = 0

    # Deducciones
    deducciones: int = 0
    bonificaciones: int = 0
    cuota_liquida: int = 0

    # Retenciones y pagos a cuenta
    retenciones: int = 0
    pagos_fraccionados: int = 0

    # Cuota diferencial
    cuota_diferencial: int = 0

    @property
    def resultado_liquidacion(self) -> int:
        """Positivo = a ingresar. Negativo = a devolver."""
        return self.cuota_diferencial


def calcular_modelo_200(
    resultado_contable: int,
    ajustes_positivos: int = 0,
    ajustes_negativos: int = 0,
    compensacion_bases_negativas: int = 0,
    tipo_impositivo: float = 25.0,
    deducciones: int = 0,
    bonificaciones: int = 0,
    retenciones: int = 0,
    pagos_fraccionados: int = 0,
) -> Modelo200:
    """Calcula el modelo 200."""
    m = Modelo200()
    m.resultado_contable = resultado_contable
    m.ajustes_positivos = ajustes_positivos
    m.ajustes_negativos = ajustes_negativos
    m.base_imponible_previa = (
        resultado_contable + ajustes_positivos - ajustes_negativos
    )
    m.compensacion_bases_negativas = compensacion_bases_negativas
    m.base_imponible = max(0, m.base_imponible_previa - compensacion_bases_negativas)
    m.tipo_impositivo = tipo_impositivo
    m.cuota_integra = int(m.base_imponible * tipo_impositivo / 100)
    m.deducciones = deducciones
    m.bonificaciones = bonificaciones
    m.cuota_liquida = m.cuota_integra - deducciones - bonificaciones
    m.retenciones = retenciones
    m.pagos_fraccionados = pagos_fraccionados
    m.cuota_diferencial = m.cuota_liquida - retenciones - pagos_fraccionados
    return m
