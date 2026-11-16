# -*- coding: utf-8 -*-
"""Modelo 303 (IVA trimestral).

Basado en la Orden EHA/3786/2008 (o la vigente).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Modelo303:
    """Liquidación trimestral del IVA."""
    # IVA repercutido (devengado)
    iva_repercutido_base: int = 0       # base imponible
    iva_repercutido_cuota: int = 0      # cuota (21%, 10%, 4%)
    iva_repercutido_total: int = 0      # base + cuota

    # IVA soportado (deducible)
    iva_soportado_base: int = 0
    iva_soportado_cuota: int = 0

    # Resultado
    diferencia: int = 0
    # 0: sin actividad, 1: a ingresar, 2: a devolver, 3: a compensar
    resultado: int = 0

    # Compensación de cuotas anteriores
    compensacion_anterior: int = 0
    compensacion_pendiente: int = 0

    @property
    def a_ingresar(self) -> int:
        return max(0, self.diferencia - self.compensacion_anterior)

    @property
    def a_devolver(self) -> int:
        return max(0, -(self.diferencia + self.compensacion_anterior))


def calcular_modelo_303(
    iva_repercutido_base: int,
    iva_repercutido_cuota: int,
    iva_soportado_base: int,
    iva_soportado_cuota: int,
    compensacion_anterior: int = 0,
) -> Modelo303:
    """Calcula el modelo 303."""
    m = Modelo303()
    m.iva_repercutido_base = iva_repercutido_base
    m.iva_repercutido_cuota = iva_repercutido_cuota
    m.iva_repercutido_total = iva_repercutido_base + iva_repercutido_cuota
    m.iva_soportado_base = iva_soportado_base
    m.iva_soportado_cuota = iva_soportado_cuota
    m.diferencia = iva_repercutido_cuota - iva_soportado_cuota
    m.compensacion_anterior = compensacion_anterior

    if m.diferencia > 0:
        m.resultado = 1  # a ingresar
    elif m.diferencia < 0:
        m.resultado = 2  # a devolver
    else:
        m.resultado = 0  # sin actividad

    if m.resultado == 2:
        m.compensacion_pendiente = abs(m.diferencia)
    elif m.resultado == 1 and compensacion_anterior > 0:
        m.compensacion_pendiente = max(0, compensacion_anterior - m.diferencia)

    return m


def calcular_desde_libros(
    lineas_iva: list[dict],
    compensacion_anterior: int = 0,
) -> Modelo303:
    """Calcula el 303 a partir de las líneas de IVA.

    Args:
        lineas_iva: lista de {cuenta, debe_centimos, haber_centimos}
        compensacion_anterior: compensación pendiente del trimestre anterior
    """
    iva_rep_base = 0
    iva_rep_cuota = 0
    iva_sop_base = 0
    iva_sop_cuota = 0
    for l in lineas_iva:
        cuenta = l["cuenta"]
        debe = l.get("debe_centimos", 0)
        haber = l.get("haber_centimos", 0)
        if cuenta == "477":  # IVA repercutido
            iva_rep_cuota += haber
        elif cuenta == "472":  # IVA soportado
            iva_sop_cuota += debe
        elif cuenta == "700" or cuenta == "705":  # ventas
            iva_rep_base += haber
        elif cuenta.startswith("6"):  # compras
            iva_sop_base += debe
    return calcular_modelo_303(
        iva_repercutido_base=iva_rep_base,
        iva_repercutido_cuota=iva_rep_cuota,
        iva_soportado_base=iva_sop_base,
        iva_soportado_cuota=iva_sop_cuota,
        compensacion_anterior=compensacion_anterior,
    )
