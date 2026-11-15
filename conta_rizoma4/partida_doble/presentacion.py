# -*- coding: utf-8 -*-
"""Presentación formateada del balance y PyG por grupos PGC.

A diferencia de `cuentas_anuales.py` (que agrupa por naturaleza y da
subtotales), esta presentación muestra los asientos agrupados por
grupos 1-5 del PGC (balance) y 6-7 (PyG), con subtotales por grupo
y totales globales.

Formato de salida:
  BALANCE DE SITUACIÓN (agrupado por grupos PGC)
  ACTIVO:
    Grupo 1 - Financiación básica: ...
    Grupo 2 - Inmovilizado: ...
    ...
  PASIVO + PN:
    ...
  Resultado del ejercicio: ...
"""
from __future__ import annotations

from .libro_mayor import mayor


_GRUPOS_ACTIVO = {
    1: "Financiación básica",
    2: "Inmovilizado",
    3: "Existencias",
    4: "Acreedores y deudores",
    5: "Cuentas financieras",
}

_GRUPOS_PYG = {
    6: "Compras y gastos",
    7: "Ventas e ingresos",
}

# Cuentas correctoras del activo (mismo criterio que cuentas_anuales)
_CORRECTORES_ACTIVO = ("28", "29", "39", "49", "59")


def _es_corrector(cuenta: str) -> bool:
    return any(cuenta.startswith(p) for p in _CORRECTORES_ACTIVO)


def balance_formateado(repo, desde=None, hasta=None):
    """Balance agrupado por grupos 1-5 del PGC.

    Devuelve:
      {
        "activo": {grupo_num: {cuenta: importe_centimos}},
        "pasivo": {grupo_num: {cuenta: importe_centimos}},
        "correctores": {cuenta: importe_centimos},
        "resultado_ejercicio": int,
        "total_activo": int,
        "total_pasivo": int,
        "total_pasivo_mas_resultado": int,
        "cuadra": bool,
      }
    """
    mayor_data = mayor(repo, desde, hasta)
    activo = {1: {}, 2: {}, 3: {}, 4: {}, 5: {}}
    pasivo = {1: {}, 2: {}, 3: {}, 4: {}, 5: {}}
    correctores = {}
    gastos_total = 0
    ingresos_total = 0

    for cuenta, datos in mayor_data.items():
        if not cuenta or not cuenta[0].isdigit():
            continue
        grupo = int(cuenta[0])
        saldo = datos["saldo"]
        if saldo == 0:
            continue
        if grupo in (1, 2, 3, 4, 5):
            if _es_corrector(cuenta):
                correctores[cuenta] = abs(saldo)
            elif saldo > 0:
                activo[grupo][cuenta] = saldo
            else:
                pasivo[grupo][cuenta] = -saldo
        elif grupo == 6:
            gastos_total += saldo
        elif grupo == 7:
            ingresos_total += -saldo

    resultado = ingresos_total - gastos_total
    total_activo = (
        sum(sum(g.values()) for g in activo.values())
        - sum(correctores.values())
    )
    total_pasivo = sum(sum(g.values()) for g in pasivo.values())

    return {
        "activo": activo,
        "pasivo": pasivo,
        "correctores": correctores,
        "resultado_ejercicio": resultado,
        "total_activo": total_activo,
        "total_pasivo": total_pasivo,
        "total_pasivo_mas_resultado": total_pasivo + resultado,
        "cuadra": total_activo == total_pasivo + resultado,
    }


def pyg_formateado(repo, desde=None, hasta=None):
    """PyG agrupada por grupos 6-7 del PGC.

    Devuelve:
      {
        "gastos": {cuenta: importe_centimos},
        "ingresos": {cuenta: importe_centimos},
        "total_gastos": int,
        "total_ingresos": int,
        "resultado": int,
      }
    """
    mayor_data = mayor(repo, desde, hasta)
    gastos = {}
    ingresos = {}
    for cuenta, datos in mayor_data.items():
        if not cuenta or not cuenta[0].isdigit():
            continue
        grupo = int(cuenta[0])
        saldo = datos["saldo"]
        if saldo == 0:
            continue
        if grupo == 6:
            gastos[cuenta] = saldo
        elif grupo == 7:
            ingresos[cuenta] = -saldo
    return {
        "gastos": gastos,
        "ingresos": ingresos,
        "total_gastos": sum(gastos.values()),
        "total_ingresos": sum(ingresos.values()),
        "resultado": sum(ingresos.values()) - sum(gastos.values()),
    }
