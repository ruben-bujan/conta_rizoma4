# -*- coding: utf-8 -*-
"""ECPN (Estado de Cambios en el Patrimonio Neto).

Dos partes:
  A) Estado de ingresos y gastos reconocidos.
  B) Estado total de cambios en el patrimonio neto.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ECPN:
    """Estado de Cambios en el Patrimonio Neto."""
    # A) Estado de ingresos y gastos reconocidos
    resultado_cuenta_pyg: int = 0
    ingresos_gastos_imputados_pn: list[dict] = field(default_factory=list)
    transferencias_a_pyg: list[dict] = field(default_factory=list)

    # B) Estado total de cambios en el patrimonio neto
    saldo_inicial: int = 0
    ajustes_por_cambios_criterio: int = 0
    ajustes_por_errores: int = 0
    saldo_inicial_ajustado: int = 0
    total_ingresos_gastos_reconocidos: int = 0
    operaciones_con_socios: list[dict] = field(default_factory=list)
    otras_variaciones: int = 0
    saldo_final: int = 0


def formatear_ecpn(
    resultado_ejercicio: int,
    saldo_inicial_pn: int,
    variaciones_pn: list[dict],
) -> ECPN:
    """Construye el ECPN.

    Args:
        resultado_ejercicio: resultado de PyG del ejercicio
        saldo_inicial_pn: patrimonio neto al inicio
        variaciones_pn: lista de {concepto, importe}
    """
    e = ECPN()
    e.resultado_cuenta_pyg = resultado_ejercicio
    e.saldo_inicial = saldo_inicial_pn
    e.saldo_inicial_ajustado = saldo_inicial_pn
    total_variaciones = sum(v["importe"] for v in variaciones_pn)
    e.operaciones_con_socios = variaciones_pn
    e.total_ingresos_gastos_reconocidos = resultado_ejercicio
    e.saldo_final = saldo_inicial_pn + resultado_ejercicio + total_variaciones
    return e
