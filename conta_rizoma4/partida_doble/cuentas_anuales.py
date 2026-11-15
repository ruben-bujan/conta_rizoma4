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


_CORRECTORES_ACTIVO_PREFIJOS = ("28", "29", "39", "49", "59")


def _es_corrector_activo(cuenta: str) -> bool:
    return any(cuenta.startswith(p) for p in _CORRECTORES_ACTIVO_PREFIJOS)


def balance_situacion(repo, desde=None, hasta=None):
    """Balance de situación: activo (neto) vs pasivo + PN + resultado.

    Los correctores del activo (281, 291, 391, 491, 591) se restan del
    activo bruto. No aparecen como pasivo.
    """
    mayor_data = mayor(repo, desde, hasta)
    activo_bruto = {}
    correctores = {}
    pasivo = {}
    gastos_total = 0
    ingresos_total = 0

    for cuenta, datos in mayor_data.items():
        grupo = _grupo(cuenta)
        saldo = datos["saldo"]
        if grupo in (1, 2, 3, 4, 5):
            if _es_corrector_activo(cuenta):
                if saldo != 0:
                    correctores[cuenta] = abs(saldo)
            else:
                if saldo > 0:
                    activo_bruto[cuenta] = saldo
                elif saldo < 0:
                    pasivo[cuenta] = -saldo
        elif grupo == 6:
            gastos_total += saldo
        elif grupo == 7:
            ingresos_total += -saldo

    resultado = ingresos_total - gastos_total
    total_activo_bruto = sum(activo_bruto.values())
    total_correctores = sum(correctores.values())
    total_activo_neto = total_activo_bruto - total_correctores
    total_pasivo = sum(pasivo.values())

    return {
        "activo": activo_bruto,
        "correctores": correctores,
        "pasivo": pasivo,
        "resultado_ejercicio": resultado,
        "total_activo_bruto": total_activo_bruto,
        "total_correctores": total_correctores,
        "total_activo": total_activo_neto,
        "total_pasivo": total_pasivo,
        "total_pasivo_mas_resultado": total_pasivo + resultado,
        "cuadra": total_activo_neto == total_pasivo + resultado,
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
