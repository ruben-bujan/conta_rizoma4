# -*- coding: utf-8 -*-
"""Existencias avanzado: corrección valorativa, deterioro reversible."""
from __future__ import annotations

from ..partida_doble.modelo import Asiento, Linea
from ..partida_doble.creacion import crear_asiento


def _asiento(*, indice, hash_previo, fecha, concepto, lineas, metadatos=None):
    return crear_asiento(
        indice=indice, fecha=fecha, concepto=concepto,
        lineas=lineas, hash_previo=hash_previo, metadatos=metadatos,
    )


def correccion_valorativa_existencias(
    *, indice, hash_previo, fecha, importe_centimos,
    concepto="Corrección valorativa de existencias",
) -> Asiento:
    """A_CORRECCION_VALORATIVA_EXISTENCIAS.

    Debe:  693
    Haber: 390
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("693", debe_centimos=importe_centimos),
            Linea("390", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_CORRECCION_VALORATIVA_EXISTENCIAS"},
    )


def deterioro_reversible_existencias(
    *, indice, hash_previo, fecha, importe_centimos,
    concepto="Reversión deterioro existencias",
) -> Asiento:
    """A_DETERIORO_REVERSIBLE_EXISTENCIAS.

    Debe:  390
    Haber: 793
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("390", debe_centimos=importe_centimos),
            Linea("793", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_DETERIORO_REVERSIBLE_EXISTENCIAS"},
    )


def regularizacion_existencias_fifo(
    *, indice, hash_previo, fecha, saldo_inicial_centimos,
    saldo_final_fifo_centimos, concepto="Regularización FIFO",
) -> Asiento:
    """A_REGULARIZACION_EXISTENCIAS_FIFO (FIFO: coste real de lo vendido)."""
    diff = saldo_final_fifo_centimos - saldo_inicial_centimos
    if diff == 0:
        raise ValueError("sin variación")
    if diff > 0:
        lineas = [
            Linea("300", debe_centimos=diff),
            Linea("610", haber_centimos=diff),
        ]
    else:
        lineas = [
            Linea("610", debe_centimos=-diff),
            Linea("300", haber_centimos=-diff),
        ]
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=lineas,
        metadatos={"codigo": "A_REGULARIZACION_EXISTENCIAS_FIFO", "metodo": "FIFO"},
    )


ACTOS = {
    "A_CORRECCION_VALORATIVA_EXISTENCIAS": correccion_valorativa_existencias,
    "A_DETERIORO_REVERSIBLE_EXISTENCIAS": deterioro_reversible_existencias,
    "A_REGULARIZACION_EXISTENCIAS_FIFO": regularizacion_existencias_fifo,
}


def crear_acto_existencias_avanzado(codigo: str, **params) -> Asiento:
    if codigo not in ACTOS:
        raise ValueError(f"Acto existencias avanzado desconocido: {codigo}")
    return ACTOS[codigo](**params)
