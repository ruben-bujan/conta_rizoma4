# -*- coding: utf-8 -*-
"""Actos de inmovilizado: compra, venta, amortización, deterioro, leasing."""
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


def compra_inmov_material(
    *, indice, hash_previo, fecha, base_centimos, iva_pct,
    cuenta_inmov, proveedor_nif, concepto,
) -> Asiento:
    """A_COMPRA_INMOV_MATERIAL.

    Debe:  {cuenta_inmov}, 472
    Haber: 400
    """
    iva = _pct(base_centimos, iva_pct)
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea(cuenta_inmov, debe_centimos=base_centimos),
            Linea("472", debe_centimos=iva),
            Linea("400", haber_centimos=base_centimos + iva,
                  concepto_linea=f"Proveedor {proveedor_nif}"),
        ],
        metadatos={"codigo": "A_COMPRA_INMOV_MATERIAL", "iva_pct": iva_pct},
    )


def venta_inmovilizado(
    *, indice, hash_previo, fecha, precio_centimos, iva_pct,
    cuenta_inmov, amort_acumulada_centimos, valor_neto_contable_centimos,
    cliente_nif, concepto,
) -> Asiento:
    """A_VENTA_INMOVILIZADO.

    Debe:  572/430 (precio+IVA), 28x (amort. acumulada)
    Haber: 21x (coste), 477 (IVA), 771 (beneficio) si procede
    O bien Debe 671 (pérdida) si procede.

    Args:
        precio_centimos: precio de venta SIN IVA
        valor_neto_contable_centimos: coste - amort_acumulada
    """
    iva = _pct(precio_centimos, iva_pct)
    total_cliente = precio_centimos + iva
    beneficio = precio_centimos - valor_neto_contable_centimos
    lineas = [
        Linea("430", debe_centimos=total_cliente,
              concepto_linea=f"Cliente {cliente_nif}"),
        Linea("28", debe_centimos=amort_acumulada_centimos,
              concepto_linea="Amortización acumulada"),
        Linea(cuenta_inmov, haber_centimos=amort_acumulada_centimos + valor_neto_contable_centimos,
              concepto_linea="Baja del inmovilizado"),
        Linea("477", haber_centimos=iva),
    ]
    if beneficio > 0:
        lineas.append(Linea("771", haber_centimos=beneficio))
    elif beneficio < 0:
        lineas.append(Linea("671", debe_centimos=-beneficio))
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=lineas,
        metadatos={"codigo": "A_VENTA_INMOVILIZADO", "beneficio": beneficio},
    )


def amortizacion_anual(
    *, indice, hash_previo, fecha, importe_centimos,
    cuenta_gasto, cuenta_amort, concepto="Amortización anual",
) -> Asiento:
    """A_AMORTIZACION_ANUAL.

    Debe:  68x
    Haber: 28x
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea(cuenta_gasto, debe_centimos=importe_centimos),
            Linea(cuenta_amort, haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_AMORTIZACION_ANUAL"},
    )


def deterioro_inmovilizado(
    *, indice, hash_previo, fecha, importe_centimos, concepto="Deterioro",
) -> Asiento:
    """A_DETERIORO_INMOVILIZADO.

    Debe:  691
    Haber: 291
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("691", debe_centimos=importe_centimos),
            Linea("291", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_DETERIORO_INMOVILIZADO"},
    )


def baja_inmovilizado(
    *, indice, hash_previo, fecha, cuenta_inmov,
    amort_acumulada_centimos, valor_neto_contable_centimos,
    concepto="Baja del inmovilizado",
) -> Asiento:
    """A_BAJA_INMOVILIZADO (sin venta, por siniestro o desuso).

    Debe:  28x (amort acumulada), 671 (pérdida = valor neto)
    Haber: 21x (coste)
    """
    lineas = [
        Linea("28", debe_centimos=amort_acumulada_centimos),
        Linea(cuenta_inmov,
              haber_centimos=amort_acumulada_centimos + valor_neto_contable_centimos),
    ]
    if valor_neto_contable_centimos > 0:
        lineas.append(Linea("671", debe_centimos=valor_neto_contable_centimos))
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=lineas,
        metadatos={"codigo": "A_BAJA_INMOVILIZADO"},
    )


ACTOS = {
    "A_COMPRA_INMOV_MATERIAL": compra_inmov_material,
    "A_VENTA_INMOVILIZADO": venta_inmovilizado,
    "A_AMORTIZACION_ANUAL": amortizacion_anual,
    "A_DETERIORO_INMOVILIZADO": deterioro_inmovilizado,
    "A_BAJA_INMOVILIZADO": baja_inmovilizado,
}


def crear_acto_inmov(codigo: str, **params) -> Asiento:
    if codigo not in ACTOS:
        raise ValueError(f"Acto inmovilizado desconocido: {codigo}")
    return ACTOS[codigo](**params)
