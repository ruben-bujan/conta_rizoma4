# -*- coding: utf-8 -*-
"""Actos de existencias: compra, venta, regularización, deterioro."""
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


def compra_existencias(
    *, indice, hash_previo, fecha, base_centimos, iva_pct,
    cuenta_compra, proveedor_nif, concepto,
) -> Asiento:
    """A_COMPRA_EXISTENCIAS.

    Debe:  {cuenta_compra} (600/601/602), 472
    Haber: 400
    """
    iva = _pct(base_centimos, iva_pct)
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea(cuenta_compra, debe_centimos=base_centimos),
            Linea("472", debe_centimos=iva),
            Linea("400", haber_centimos=base_centimos + iva,
                  concepto_linea=f"Proveedor {proveedor_nif}"),
        ],
        metadatos={"codigo": "A_COMPRA_EXISTENCIAS", "iva_pct": iva_pct},
    )


def venta_existencias(
    *, indice, hash_previo, fecha, base_centimos, iva_pct,
    cliente_nif, concepto,
) -> Asiento:
    """A_VENTA_EXISTENCIAS.

    Debe:  430
    Haber: 700, 477
    """
    iva = _pct(base_centimos, iva_pct)
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("430", debe_centimos=base_centimos + iva,
                  concepto_linea=f"Cliente {cliente_nif}"),
            Linea("700", haber_centimos=base_centimos),
            Linea("477", haber_centimos=iva),
        ],
        metadatos={"codigo": "A_VENTA_EXISTENCIAS", "iva_pct": iva_pct},
    )


def regularizacion_existencias(
    *, indice, hash_previo, fecha, saldo_inicial_centimos,
    saldo_final_centimos, concepto="Variación de existencias",
) -> Asiento:
    """A_REGULARIZACION_EXISTENCIAS.

    Si saldo_final > saldo_inicial: 300 D (aumento)
    Si saldo_final < saldo_inicial: 300 H (disminución)
    Contrapartida: 610 (variación)
    """
    diff = saldo_final_centimos - saldo_inicial_centimos
    lineas = []
    if diff > 0:
        lineas.append(Linea("300", debe_centimos=diff))
        lineas.append(Linea("610", haber_centimos=diff))
    elif diff < 0:
        lineas.append(Linea("610", debe_centimos=-diff))
        lineas.append(Linea("300", haber_centimos=-diff))
    else:
        raise ValueError("sin variación: saldo_inicial == saldo_final")
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=lineas,
        metadatos={"codigo": "A_REGULARIZACION_EXISTENCIAS", "diff": diff},
    )


def deterioro_existencias(
    *, indice, hash_previo, fecha, importe_centimos,
    concepto="Deterioro de existencias",
) -> Asiento:
    """A_DETERIORO_EXISTENCIAS.

    Debe:  693
    Haber: 390
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("693", debe_centimos=importe_centimos),
            Linea("390", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_DETERIORO_EXISTENCIAS"},
    )


ACTOS = {
    "A_COMPRA_EXISTENCIAS": compra_existencias,
    "A_VENTA_EXISTENCIAS": venta_existencias,
    "A_REGULARIZACION_EXISTENCIAS": regularizacion_existencias,
    "A_DETERIORO_EXISTENCIAS": deterioro_existencias,
}


def crear_acto_existencias(codigo: str, **params) -> Asiento:
    if codigo not in ACTOS:
        raise ValueError(f"Acto existencias desconocido: {codigo}")
    return ACTOS[codigo](**params)
