# -*- coding: utf-8 -*-
"""Actos de ajuste: subvenciones, periodificaciones, moneda, provisiones."""
from __future__ import annotations

from ..partida_doble.modelo import Asiento, Linea
from ..partida_doble.creacion import crear_asiento


def _asiento(*, indice, hash_previo, fecha, concepto, lineas, metadatos=None):
    return crear_asiento(
        indice=indice, fecha=fecha, concepto=concepto,
        lineas=lineas, hash_previo=hash_previo, metadatos=metadatos,
    )


# ─── Subvenciones ─────────────────────────────────────────────────

def subvencion_capital_cobro(
    *, indice, hash_previo, fecha, importe_centimos,
    concepto="Subvención de capital",
) -> Asiento:
    """A_SUBVENCION_CAPITAL_COBRO.

    Debe:  572
    Haber: 130
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("572", debe_centimos=importe_centimos),
            Linea("130", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_SUBVENCION_CAPITAL_COBRO"},
    )


def subvencion_capital_imputacion(
    *, indice, hash_previo, fecha, importe_centimos,
    concepto="Imputación subvención de capital",
) -> Asiento:
    """A_SUBVENCION_CAPITAL_IMPUTACION.

    Debe:  130
    Haber: 746
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("130", debe_centimos=importe_centimos),
            Linea("746", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_SUBVENCION_CAPITAL_IMPUTACION"},
    )


def subvencion_explotacion(
    *, indice, hash_previo, fecha, importe_centimos,
    concepto="Subvención de explotación",
) -> Asiento:
    """A_SUBVENCION_EXPLOTACION.

    Debe:  572
    Haber: 740
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("572", debe_centimos=importe_centimos),
            Linea("740", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_SUBVENCION_EXPLOTACION"},
    )


# ─── Periodificaciones ────────────────────────────────────────────

def periodificacion_gasto_anticipado(
    *, indice, hash_previo, fecha, importe_centimos,
    cuenta_gasto, concepto="Gasto anticipado",
) -> Asiento:
    """A_PERIODIFICACION_GASTO_ANTICIPADO.

    Debe:  480
    Haber: {cuenta_gasto}
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("480", debe_centimos=importe_centimos),
            Linea(cuenta_gasto, haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_PERIODIFICACION_GASTO_ANTICIPADO"},
    )


def periodificacion_ingreso_anticipado(
    *, indice, hash_previo, fecha, importe_centimos,
    cuenta_ingreso, concepto="Ingreso anticipado",
) -> Asiento:
    """A_PERIODIFICACION_INGRESO_ANTICIPADO.

    Debe:  {cuenta_ingreso}
    Haber: 485
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea(cuenta_ingreso, debe_centimos=importe_centimos),
            Linea("485", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_PERIODIFICACION_INGRESO_ANTICIPADO"},
    )


# ─── Moneda extranjera ───────────────────────────────────────────

def dif_cambio_positiva(
    *, indice, hash_previo, fecha, importe_centimos,
    concepto="Diferencia de cambio positiva",
) -> Asiento:
    """A_DIFERENCIA_CAMBIO_POSITIVA.

    Debe:  572
    Haber: 768
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("572", debe_centimos=importe_centimos),
            Linea("768", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_DIFERENCIA_CAMBIO_POSITIVA"},
    )


def dif_cambio_negativa(
    *, indice, hash_previo, fecha, importe_centimos,
    concepto="Diferencia de cambio negativa",
) -> Asiento:
    """A_DIFERENCIA_CAMBIO_NEGATIVA.

    Debe:  668
    Haber: 572
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("668", debe_centimos=importe_centimos),
            Linea("572", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_DIFERENCIA_CAMBIO_NEGATIVA"},
    )


# ─── Provisiones ─────────────────────────────────────────────────

def provision_garantia(
    *, indice, hash_previo, fecha, importe_centimos,
    concepto="Provisión para garantías",
) -> Asiento:
    """A_PROVISION_GARANTIA.

    Debe:  660
    Haber: 143
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("660", debe_centimos=importe_centimos),
            Linea("143", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_PROVISION_GARANTIA"},
    )


def provision_litigio(
    *, indice, hash_previo, fecha, importe_centimos,
    concepto="Provisión para litigio",
) -> Asiento:
    """A_PROVISION_LITIGIO.

    Debe:  660
    Haber: 142
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("660", debe_centimos=importe_centimos),
            Linea("142", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_PROVISION_LITIGIO"},
    )


ACTOS = {
    "A_SUBVENCION_CAPITAL_COBRO": subvencion_capital_cobro,
    "A_SUBVENCION_CAPITAL_IMPUTACION": subvencion_capital_imputacion,
    "A_SUBVENCION_EXPLOTACION": subvencion_explotacion,
    "A_PERIODIFICACION_GASTO_ANTICIPADO": periodificacion_gasto_anticipado,
    "A_PERIODIFICACION_INGRESO_ANTICIPADO": periodificacion_ingreso_anticipado,
    "A_DIFERENCIA_CAMBIO_POSITIVA": dif_cambio_positiva,
    "A_DIFERENCIA_CAMBIO_NEGATIVA": dif_cambio_negativa,
    "A_PROVISION_GARANTIA": provision_garantia,
    "A_PROVISION_LITIGIO": provision_litigio,
}


def crear_acto_ajuste(codigo: str, **params) -> Asiento:
    if codigo not in ACTOS:
        raise ValueError(f"Acto de ajuste desconocido: {codigo}")
    return ACTOS[codigo](**params)
