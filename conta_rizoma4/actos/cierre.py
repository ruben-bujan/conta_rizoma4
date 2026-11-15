# -*- coding: utf-8 -*-
"""Actos de cierre de ejercicio: regularización, cierre, apertura."""
from __future__ import annotations

from datetime import date

from ..partida_doble.modelo import Asiento, Linea
from ..partida_doble.creacion import crear_asiento


def _asiento(*, indice, hash_previo, fecha, concepto, lineas, metadatos=None):
    return crear_asiento(
        indice=indice, fecha=fecha, concepto=concepto,
        lineas=lineas, hash_previo=hash_previo, metadatos=metadatos,
    )


def regularizacion_grupos_6_7(
    *, indice, hash_previo, fecha, saldos_grupo_6_7,
    concepto="Regularización grupos 6 y 7",
) -> Asiento:
    """A_REGULARIZACION_GRUPOS_6_7.

    Cierra las cuentas de gastos (grupo 6) e ingresos (grupo 7)
    contra 129 (Resultado del ejercicio).

    Args:
        saldos_grupo_6_7: dict {cuenta: saldo_centimos}.
                         Positivo = saldo acreedor (ingreso).
                         Negativo = saldo deudor (gasto).
    """
    lineas = []
    for cuenta, saldo in saldos_grupo_6_7.items():
        if saldo == 0:
            continue
        if saldo > 0:
            # Saldo acreedor (ingreso): debe para cerrar
            lineas.append(Linea(cuenta, debe_centimos=saldo))
        else:
            # Saldo deudor (gasto): haber para cerrar
            lineas.append(Linea(cuenta, haber_centimos=-saldo))
    total_debe = sum(l.debe_centimos for l in lineas)
    total_haber = sum(l.haber_centimos for l in lineas)
    if total_debe == total_haber:
        # Sin resultado: nada que regularizar
        raise ValueError("sin resultado: debe == haber, no hay nada que cerrar")
    if total_debe > total_haber:
        # Beneficio: 129 al haber
        lineas.append(Linea("129", haber_centimos=total_debe - total_haber))
    else:
        # Pérdida: 129 al debe
        lineas.append(Linea("129", debe_centimos=total_haber - total_debe))
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=lineas,
        metadatos={"codigo": "A_REGULARIZACION_GRUPOS_6_7"},
    )


def cierre_ejercicio(
    *, indice, hash_previo, fecha, saldos_balance,
    concepto="Asiento de cierre",
) -> Asiento:
    """A_CIERRE_EJERCICIO.

    Cierra todas las cuentas de balance (grupos 1-5) y la 129.

    Args:
        saldos_balance: dict {cuenta: saldo_centimos}.
                       Positivo = saldo acreedor (pasivo/PN).
                       Negativo = saldo deudor (activo).
    """
    lineas = []
    for cuenta, saldo in saldos_balance.items():
        if saldo == 0:
            continue
        if saldo > 0:
            lineas.append(Linea(cuenta, debe_centimos=saldo))
        else:
            lineas.append(Linea(cuenta, haber_centimos=-saldo))
    total_debe = sum(l.debe_centimos for l in lineas)
    total_haber = sum(l.haber_centimos for l in lineas)
    if total_debe != total_haber:
        raise ValueError(
            f"cierre descuadrado: debe={total_debe} haber={total_haber}"
        )
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=lineas,
        metadatos={"codigo": "A_CIERRE_EJERCICIO"},
    )


def apertura_ejercicio(
    *, indice, hash_previo, fecha, saldos_balance,
    concepto="Asiento de apertura",
) -> Asiento:
    """A_APERTURA_EJERCICIO.

    Inverso del cierre: abre las cuentas de balance del nuevo ejercicio.
    """
    lineas = []
    for cuenta, saldo in saldos_balance.items():
        if saldo == 0:
            continue
        if saldo > 0:
            lineas.append(Linea(cuenta, haber_centimos=saldo))
        else:
            lineas.append(Linea(cuenta, debe_centimos=-saldo))
    total_debe = sum(l.debe_centimos for l in lineas)
    total_haber = sum(l.haber_centimos for l in lineas)
    if total_debe != total_haber:
        raise ValueError(
            f"apertura descuadrada: debe={total_debe} haber={total_haber}"
        )
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=lineas,
        metadatos={"codigo": "A_APERTURA_EJERCICIO"},
    )


ACTOS = {
    "A_REGULARIZACION_GRUPOS_6_7": regularizacion_grupos_6_7,
    "A_CIERRE_EJERCICIO": cierre_ejercicio,
    "A_APERTURA_EJERCICIO": apertura_ejercicio,
}


def crear_acto_cierre(codigo: str, **params) -> Asiento:
    if codigo not in ACTOS:
        raise ValueError(f"Acto de cierre desconocido: {codigo}")
    return ACTOS[codigo](**params)
