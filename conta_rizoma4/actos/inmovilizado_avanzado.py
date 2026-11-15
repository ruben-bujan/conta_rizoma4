# -*- coding: utf-8 -*-
"""Inmovilizado avanzado: leasing, permuta, activos para venta, etc."""
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


def leasing_financiero_inicio(
    *, indice, hash_previo, fecha, valor_razonable_centimos,
    iva_pct, cuota_largo_plazo_centimos, cuota_corto_plazo_centimos,
    cuenta_inmov, proveedor_nif, concepto="Leasing financiero - inicio",
) -> Asiento:
    """A_LEASING_FINANCIERO_INICIO.

    Debe:  {cuenta_inmov}, 472
    Haber: 174 (acreedor L/P), 524 (acreedor C/P)
    """
    iva = _pct(valor_razonable_centimos, iva_pct)
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea(cuenta_inmov, debe_centimos=valor_razonable_centimos),
            Linea("472", debe_centimos=iva),
            Linea("174", haber_centimos=cuota_largo_plazo_centimos),
            Linea("524", haber_centimos=cuota_corto_plazo_centimos),
        ],
        metadatos={"codigo": "A_LEASING_FINANCIERO_INICIO"},
    )


def leasing_financiero_cuota(
    *, indice, hash_previo, fecha, cuota_centimos, interes_centimos,
    iva_pct, concepto="Cuota leasing",
) -> Asiento:
    """A_LEASING_FINANCIERO_CUOTA.

    Debe:  524 (amortización), 662 (intereses), 472 (IVA)
    Haber: 572
    """
    iva = _pct(cuota_centimos, iva_pct)
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("524", debe_centimos=cuota_centimos - interes_centimos),
            Linea("662", debe_centimos=interes_centimos),
            Linea("472", debe_centimos=iva),
            Linea("572", haber_centimos=cuota_centimos + iva),
        ],
        metadatos={"codigo": "A_LEASING_FINANCIERO_CUOTA"},
    )


def permuta_inmovilizado(
    *, indice, hash_previo, fecha, valor_razonable_recibido_centimos,
    valor_neto_contable_entregado_centimos, cuenta_inmov_entregado,
    cuenta_inmov_recibido, concepto="Permuta de inmovilizado",
) -> Asiento:
    """A_PERMUTA_INMOVILIZADO.

    Debe:  {cuenta_inmov_recibido}, 28x (amort entregado)
    Haber: {cuenta_inmov_entregado}, 771 (beneficio) o 671 (pérdida)
    """
    diff = valor_razonable_recibido_centimos - valor_neto_contable_entregado_centimos
    lineas = [
        Linea(cuenta_inmov_recibido, debe_centimos=valor_razonable_recibido_centimos),
        Linea(cuenta_inmov_entregado, haber_centimos=valor_neto_contable_entregado_centimos),
    ]
    if diff > 0:
        lineas.append(Linea("771", haber_centimos=diff))
    elif diff < 0:
        lineas.append(Linea("671", debe_centimos=-diff))
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=lineas,
        metadatos={"codigo": "A_PERMUTA_INMOVILIZADO"},
    )


def reclasificar_activo_para_venta(
    *, indice, hash_previo, fecha, importe_centimos,
    cuenta_inmov_origen, concepto="Reclasificar a activo para venta",
) -> Asiento:
    """A_RECLASIFICAR_ACTIVO_PARA_VENTA.

    Debe:  580 (activo no corriente para venta)
    Haber: {cuenta_inmov_origen}
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("580", debe_centimos=importe_centimos),
            Linea(cuenta_inmov_origen, haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_RECLASIFICAR_ACTIVO_PARA_VENTA"},
    )


def deterioro_reversible_inmov(
    *, indice, hash_previo, fecha, importe_centimos,
    cuenta_deterioro="291", concepto="Deterioro reversible",
) -> Asiento:
    """A_DETERIORO_REVERSIBLE_INMOV (reversión de deterioro).

    Debe:  {cuenta_deterioro}
    Haber: 791 (reversión)
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea(cuenta_deterioro, debe_centimos=importe_centimos),
            Linea("791", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_DETERIORO_REVERSIBLE_INMOV"},
    )


def actualizacion_valor_inmov(
    *, indice, hash_previo, fecha, importe_centimos,
    cuenta_inmov, concepto="Actualización de valor (Ley 16/2012)",
) -> Asiento:
    """A_ACTUALIZACION_VALOR_INMOV.

    Debe:  {cuenta_inmov}
    Haber: 113 (reservas por actualización) o 134 (ajuste por valoración)
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea(cuenta_inmov, debe_centimos=importe_centimos),
            Linea("134", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_ACTUALIZACION_VALOR_INMOV"},
    )


ACTOS = {
    "A_LEASING_FINANCIERO_INICIO": leasing_financiero_inicio,
    "A_LEASING_FINANCIERO_CUOTA": leasing_financiero_cuota,
    "A_PERMUTA_INMOVILIZADO": permuta_inmovilizado,
    "A_RECLASIFICAR_ACTIVO_PARA_VENTA": reclasificar_activo_para_venta,
    "A_DETERIORO_REVERSIBLE_INMOV": deterioro_reversible_inmov,
    "A_ACTUALIZACION_VALOR_INMOV": actualizacion_valor_inmov,
}


def crear_acto_inmov_avanzado(codigo: str, **params) -> Asiento:
    if codigo not in ACTOS:
        raise ValueError(f"Acto inmovilizado avanzado desconocido: {codigo}")
    return ACTOS[codigo](**params)
