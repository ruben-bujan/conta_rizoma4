# -*- coding: utf-8 -*-
"""Actos de facturación avanzada: simplificadas, autofactura, descuentos."""
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


def fact_emit_simplificada(
    *, indice, hash_previo, fecha, base_centimos, iva_pct,
    cliente_nif, concepto,
) -> Asiento:
    """A_FACT_EMIT_SIMPLIFICADA (ticket, sin retención).

    Debe:  430
    Haber: 705, 477
    """
    iva = _pct(base_centimos, iva_pct)
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("430", debe_centimos=base_centimos + iva,
                  concepto_linea=f"Cliente {cliente_nif}"),
            Linea("705", haber_centimos=base_centimos),
            Linea("477", haber_centimos=iva),
        ],
        metadatos={"codigo": "A_FACT_EMIT_SIMPLIFICADA", "iva_pct": iva_pct},
    )


def autofactura(
    *, indice, hash_previo, fecha, base_centimos, iva_pct,
    proveedor_nif, concepto,
) -> Asiento:
    """A_AUTOFACTURA (el cliente emite la factura al proveedor).

    Debe:  {cuenta_gasto}, 472
    Haber: 400
    """
    iva = _pct(base_centimos, iva_pct)
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("629", debe_centimos=base_centimos),
            Linea("472", debe_centimos=iva),
            Linea("400", haber_centimos=base_centimos + iva,
                  concepto_linea=f"Proveedor {proveedor_nif}"),
        ],
        metadatos={"codigo": "A_AUTOFACTURA", "iva_pct": iva_pct},
    )


def fact_emit_con_descuento(
    *, indice, hash_previo, fecha, base_centimos, descuento_pct, iva_pct,
    cliente_nif, concepto,
) -> Asiento:
    """A_FACT_EMIT_CON_DESCUENTO (descuento comercial en factura).

    Debe:  430 (base - desc + IVA de (base - desc))
    Haber: 705 (base), 709 (descuento), 477 (IVA)
    """
    desc = _pct(base_centimos, descuento_pct)
    base_neta = base_centimos - desc
    iva = _pct(base_neta, iva_pct)
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("430", debe_centimos=base_neta + iva,
                  concepto_linea=f"Cliente {cliente_nif}"),
            Linea("705", haber_centimos=base_centimos),
            Linea("709", debe_centimos=desc),
            Linea("477", haber_centimos=iva),
        ],
        metadatos={"codigo": "A_FACT_EMIT_CON_DESCUENTO",
                   "descuento_pct": descuento_pct, "iva_pct": iva_pct},
    )


def fact_emit_rappel(
    *, indice, hash_previo, fecha, base_centimos, rappel_pct, iva_pct,
    cliente_nif, concepto,
) -> Asiento:
    """A_FACT_EMIT_RAPPEL (descuento por volumen, fuera factura).

    Debe:  709 (rappel), 477 (IVA reverso)
    Haber: 430 (base rappel + IVA)
    """
    rappel = _pct(base_centimos, rappel_pct)
    iva = _pct(rappel, iva_pct)
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("709", debe_centimos=rappel),
            Linea("477", debe_centimos=iva),
            Linea("430", haber_centimos=rappel + iva,
                  concepto_linea=f"Cliente {cliente_nif}"),
        ],
        metadatos={"codigo": "A_FACT_EMIT_RAPPEL",
                   "rappel_pct": rappel_pct, "iva_pct": iva_pct},
    )


def fact_emit_recargo_equivalencia(
    *, indice, hash_previo, fecha, base_centimos, iva_pct, recargo_pct,
    cliente_nif, concepto,
) -> Asiento:
    """A_FACT_EMIT_RECARGO_EQUIVALENCIA (minorista, recargo).

    Debe:  430 (base + IVA + recargo)
    Haber: 705, 477, 478 (recargo de equivalencia)
    """
    iva = _pct(base_centimos, iva_pct)
    recargo = _pct(base_centimos, recargo_pct)
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("430", debe_centimos=base_centimos + iva + recargo,
                  concepto_linea=f"Cliente {cliente_nif}"),
            Linea("705", haber_centimos=base_centimos),
            Linea("477", haber_centimos=iva),
            Linea("478", haber_centimos=recargo),
        ],
        metadatos={"codigo": "A_FACT_EMIT_RECARGO_EQUIVALENCIA",
                   "iva_pct": iva_pct, "recargo_pct": recargo_pct},
    )


def aplicar_anticipo_cliente(
    *, indice, hash_previo, fecha, base_centimos, iva_pct,
    cliente_nif, concepto,
) -> Asiento:
    """A_APLICAR_ANTICIPO_CLIENTE (compensa 438 con 430 al facturar).

    Debe:  438 (cancelar anticipo)
    Haber: 430 (reducir deuda del cliente)
    """
    iva = _pct(base_centimos, iva_pct)
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("438", debe_centimos=base_centimos + iva,
                  concepto_linea=f"Cliente {cliente_nif}"),
            Linea("430", haber_centimos=base_centimos + iva,
                  concepto_linea=f"Cliente {cliente_nif}"),
        ],
        metadatos={"codigo": "A_APLICAR_ANTICIPO_CLIENTE", "iva_pct": iva_pct},
    )


def fact_emit_con_recargo_demora(
    *, indice, hash_previo, fecha, base_centimos, recargo_pct,
    cliente_nif, concepto,
) -> Asiento:
    """A_FACT_EMIT_INTERESES_DEMORA (intereses por pago tardío).

    Debe:  430 (intereses + IVA)
    Haber: 769 (ingreso), 477 (IVA)
    """
    iva = _pct(base_centimos, 21)  # IVA 21% por defecto
    interes = _pct(base_centimos, recargo_pct)
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("430", debe_centimos=interes + iva,
                  concepto_linea=f"Cliente {cliente_nif}"),
            Linea("769", haber_centimos=interes),
            Linea("477", haber_centimos=iva),
        ],
        metadatos={"codigo": "A_FACT_EMIT_INTERESES_DEMORA"},
    )


ACTOS = {
    "A_FACT_EMIT_SIMPLIFICADA": fact_emit_simplificada,
    "A_AUTOFACTURA": autofactura,
    "A_FACT_EMIT_CON_DESCUENTO": fact_emit_con_descuento,
    "A_FACT_EMIT_RAPPEL": fact_emit_rappel,
    "A_FACT_EMIT_RECARGO_EQUIVALENCIA": fact_emit_recargo_equivalencia,
    "A_APLICAR_ANTICIPO_CLIENTE": aplicar_anticipo_cliente,
    "A_FACT_EMIT_INTERESES_DEMORA": fact_emit_con_recargo_demora,
}


def crear_acto_fact_avanzada(codigo: str, **params) -> Asiento:
    if codigo not in ACTOS:
        raise ValueError(f"Acto facturación avanzada desconocido: {codigo}")
    return ACTOS[codigo](**params)
