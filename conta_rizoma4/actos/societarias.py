# -*- coding: utf-8 -*-
"""Actos societarios: constitución, ampliación, dividendos, reservas."""
from __future__ import annotations

from ..partida_doble.modelo import Asiento, Linea
from ..partida_doble.creacion import crear_asiento


def _pct(base: int, pct: float) -> int:
    return int(round(base * pct / 100))


def _asiento(*, indice, hash_previo, fecha, concepto, lineas, metadatos=None):
    return crear_asiento(
        indice=indice, fecha=fecha, concepto=concepto,
        lineas=lineas, hash_previo=hash_previo, metadatos=metadatos,
    )


def constitucion_sociedad(
    *, indice, hash_previo, fecha, capital_centimos, concepto="Constitución",
) -> Asiento:
    """A_CONSTITUCION_SOCIEDAD.

    Debe:  572
    Haber: 100
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("572", debe_centimos=capital_centimos),
            Linea("100", haber_centimos=capital_centimos),
        ],
        metadatos={"codigo": "A_CONSTITUCION_SOCIEDAD"},
    )


def ampliacion_capital(
    *, indice, hash_previo, fecha, capital_centimos, prima_centimos,
    concepto="Ampliación de capital",
) -> Asiento:
    """A_AMPLIACION_CAPITAL.

    Debe:  572 (capital + prima)
    Haber: 100 (capital), 110 (prima de emisión)
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("572", debe_centimos=capital_centimos + prima_centimos),
            Linea("100", haber_centimos=capital_centimos),
            Linea("110", haber_centimos=prima_centimos),
        ],
        metadatos={"codigo": "A_AMPLIACION_CAPITAL"},
    )


def dividendo_pagado(
    *, indice, hash_previo, fecha, dividendo_centimos, retencion_pct,
    concepto="Dividendo",
) -> Asiento:
    """A_DIVIDENDO_PAGADO.

    Debe:  129 (resultado) / 526 (dividendo a pagar)
    Haber: 526 (dividendo a pagar), 4751 (retención), 572 (neto)

    Para simplificar: se paga en el mismo acto.
    Debe:  129
    Haber: 4751 (ret), 572 (neto)
    """
    ret = _pct(dividendo_centimos, retencion_pct)
    neto = dividendo_centimos - ret
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("129", debe_centimos=dividendo_centimos),
            Linea("4751", haber_centimos=ret),
            Linea("572", haber_centimos=neto),
        ],
        metadatos={"codigo": "A_DIVIDENDO_PAGADO", "retencion_pct": retencion_pct},
    )


def reserva_legal(
    *, indice, hash_previo, fecha, importe_centimos, concepto="Reserva legal",
) -> Asiento:
    """A_RESERVA_LEGAL.

    Debe:  129
    Haber: 112
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("129", debe_centimos=importe_centimos),
            Linea("112", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_RESERVA_LEGAL"},
    )


def reduccion_capital(
    *, indice, hash_previo, fecha, importe_centimos, concepto="Reducción de capital",
) -> Asiento:
    """A_REDUCCION_CAPITAL.

    Debe:  100
    Haber: 572
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("100", debe_centimos=importe_centimos),
            Linea("572", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_REDUCCION_CAPITAL"},
    )


ACTOS = {
    "A_CONSTITUCION_SOCIEDAD": constitucion_sociedad,
    "A_AMPLIACION_CAPITAL": ampliacion_capital,
    "A_DIVIDENDO_PAGADO": dividendo_pagado,
    "A_RESERVA_LEGAL": reserva_legal,
    "A_REDUCCION_CAPITAL": reduccion_capital,
}


def crear_acto_societario(codigo: str, **params) -> Asiento:
    if codigo not in ACTOS:
        raise ValueError(f"Acto societario desconocido: {codigo}")
    return ACTOS[codigo](**params)
