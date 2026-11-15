# -*- coding: utf-8 -*-
"""Ajustes avanzados: desmantelamiento, medioambientales, coberturas, correcciones."""
from __future__ import annotations

from ..partida_doble.modelo import Asiento, Linea
from ..partida_doble.creacion import crear_asiento


def _asiento(*, indice, hash_previo, fecha, concepto, lineas, metadatos=None):
    return crear_asiento(
        indice=indice, fecha=fecha, concepto=concepto,
        lineas=lineas, hash_previo=hash_previo, metadatos=metadatos,
    )


def provision_desmantelamiento(
    *, indice, hash_previo, fecha, importe_centimos,
    cuenta_inmov, concepto="Provisión desmantelamiento",
) -> Asiento:
    """A_PROVISION_DESMANTELAMIENTO.

    Debe:  {cuenta_inmov} (se incorpora al coste del activo)
    Haber: 143 (provisión)
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea(cuenta_inmov, debe_centimos=importe_centimos),
            Linea("143", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_PROVISION_DESMANTELAMIENTO"},
    )


def provision_medioambiental(
    *, indice, hash_previo, fecha, importe_centimos,
    concepto="Provisión medioambiental",
) -> Asiento:
    """A_PROVISION_MEDIOAMBIENTAL.

    Debe:  622 (o cuenta de gasto)
    Haber: 145 (provisión)
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("622", debe_centimos=importe_centimos),
            Linea("145", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_PROVISION_MEDIOAMBIENTAL"},
    )


def cobertura_flujo_efectivo(
    *, indice, hash_previo, fecha, importe_centimos,
    cuenta_ajuste="910", concepto="Cobertura de flujos de efectivo",
) -> Asiento:
    """A_COBERTURA_FLUJO_EFECTIVO (contabilidad de coberturas).

    Debe/Haber entre cuenta de ajuste (grupo 9) y patrimonio neto (133).
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea(cuenta_ajuste, debe_centimos=importe_centimos),
            Linea("133", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_COBERTURA_FLUJO_EFECTIVO"},
    )


def correccion_error_ejercicio_anterior(
    *, indice, hash_previo, fecha, importe_centimos,
    cuenta_afectada, concepto="Corrección de error de ejercicio anterior",
) -> Asiento:
    """A_CORRECCION_ERROR_EJERCICIO_ANTERIOR.

    Debe/Haber entre cuenta afectada y 113 (reservas voluntarias).
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea(cuenta_afectada, debe_centimos=importe_centimos),
            Linea("113", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_CORRECCION_ERROR_EJERCICIO_ANTERIOR"},
    )


def cambio_criterio_contable(
    *, indice, hash_previo, fecha, importe_centimos,
    cuenta_afectada, concepto="Cambio de criterio contable",
) -> Asiento:
    """A_CAMBIO_CRITERIO_CONTABLE (ajuste retroactivo).

    Debe/Haber entre cuenta afectada y 113.
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea(cuenta_afectada, debe_centimos=importe_centimos),
            Linea("113", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_CAMBIO_CRITERIO_CONTABLE"},
    )


ACTOS = {
    "A_PROVISION_DESMANTELAMIENTO": provision_desmantelamiento,
    "A_PROVISION_MEDIOAMBIENTAL": provision_medioambiental,
    "A_COBERTURA_FLUJO_EFECTIVO": cobertura_flujo_efectivo,
    "A_CORRECCION_ERROR_EJERCICIO_ANTERIOR": correccion_error_ejercicio_anterior,
    "A_CAMBIO_CRITERIO_CONTABLE": cambio_criterio_contable,
}


def crear_acto_ajuste_avanzado(codigo: str, **params) -> Asiento:
    if codigo not in ACTOS:
        raise ValueError(f"Acto de ajuste avanzado desconocido: {codigo}")
    return ACTOS[codigo](**params)
