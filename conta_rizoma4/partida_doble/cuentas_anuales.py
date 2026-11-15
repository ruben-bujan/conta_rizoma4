# -*- coding: utf-8 -*-
"""Cuentas anuales: balance de situación + cuenta de PyG.

Modelo simplificado (abreviado). Agrupa por primer dígito del código PGC:
  - Grupos 1-5: balance (activo/pasivo/PN)
  - Grupo 6: gastos
  - Grupo 7: ingresos

Ecuación contable:
  Activo = Pasivo + PN + Resultado del ejercicio
  donde Resultado = Ingresos - Gastos

La igualdad se mantiene por construcción (cada asiento cuadra).
"""
from __future__ import annotations

from .libro_mayor import mayor


def _grupo(cuenta: str) -> int:
    if not cuenta or not cuenta[0].isdigit():
        return 0
    return int(cuenta[0])


def balance_situacion(repo, desde=None, hasta=None):
    """Balance de situación: activo vs pasivo + PN + resultado.

    Devuelve:
      {
        "activo": {cuenta: importe_centimos},
        "pasivo": {cuenta: importe_centimos},
        "resultado_ejercicio": int,
        "total_activo": int,
        "total_pasivo": int,
        "total_pasivo_mas_resultado": int,
        "cuadra": bool,
      }
    """
    mayor_data = mayor(repo, desde, hasta)
    activo = {}
    pasivo = {}
    gastos_total = 0
    ingresos_total = 0
    for cuenta, datos in mayor_data.items():
        grupo = _grupo(cuenta)
        saldo = datos["saldo"]
        if grupo in (1, 2, 3, 4, 5):
            if saldo > 0:
                activo[cuenta] = saldo
            elif saldo < 0:
                pasivo[cuenta] = -saldo
        elif grupo == 6:
            # Gasto: saldo deudor positivo
            gastos_total += saldo
        elif grupo == 7:
            # Ingreso: saldo acreedor negativo → convertir a positivo
            ingresos_total += -saldo
    resultado = ingresos_total - gastos_total
    total_activo = sum(activo.values())
    total_pasivo = sum(pasivo.values())
    return {
        "activo": activo,
        "pasivo": pasivo,
        "resultado_ejercicio": resultado,
        "total_activo": total_activo,
        "total_pasivo": total_pasivo,
        "total_pasivo_mas_resultado": total_pasivo + resultado,
        "cuadra": total_activo == total_pasivo + resultado,
    }


def cuenta_pyg(repo, desde=None, hasta=None):
    """Cuenta de pérdidas y ganancias.

    Devuelve:
      {
        "gastos": {cuenta: importe_centimos},
        "ingresos": {cuenta: importe_centimos},
        "total_gastos": int,
        "total_ingresos": int,
        "resultado": int,  # positivo = beneficio, negativo = pérdida
      }
    """
    mayor_data = mayor(repo, desde, hasta)
    gastos = {}
    ingresos = {}
    for cuenta, datos in mayor_data.items():
        grupo = _grupo(cuenta)
        saldo = datos["saldo"]
        if grupo == 6 and saldo != 0:
            gastos[cuenta] = saldo
        elif grupo == 7 and saldo != 0:
            ingresos[cuenta] = -saldo
    total_gastos = sum(gastos.values())
    total_ingresos = sum(ingresos.values())
    return {
        "gastos": gastos,
        "ingresos": ingresos,
        "total_gastos": total_gastos,
        "total_ingresos": total_ingresos,
        "resultado": total_ingresos - total_gastos,
    }
