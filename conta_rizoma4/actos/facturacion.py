# -*- coding: utf-8 -*-
"""Actos de facturación: emitidas y recibidas.

Cada función devuelve un Asiento (partida doble) a partir de parámetros
de negocio (base, tipo de IVA, tipo de retención, etc.).

Son funciones puras: no persisten. Para persistir, llamar a
`guardar_asiento(acto)` después.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Optional

from ..partida_doble.modelo import Asiento, Linea
from ..partida_doble.creacion import crear_asiento


def _pct(base_centimos: int, pct: float) -> int:
    """Calcula pct% de base_centimos, redondeado a céntimos."""
    if base_centimos < 0:
        raise ValueError(f"base_centimos negativo: {base_centimos}")
    if pct < 0 or pct > 100:
        raise ValueError(f"pct fuera de rango: {pct}")
    return int(round(base_centimos * pct / 100))


def _asiento(
    *, indice, hash_previo, fecha, concepto, lineas,
    metadatos: Optional[dict[str, Any]] = None,
) -> Asiento:
    return crear_asiento(
        indice=indice, fecha=fecha, concepto=concepto,
        lineas=lineas, hash_previo=hash_previo, metadatos=metadatos,
    )


# ─── Facturación emitida (servicios) ──────────────────────────────

def fact_emit_serv_nac_con_ret(
    *, indice, hash_previo, fecha, base_centimos, iva_pct, retencion_pct,
    cliente_nif, concepto,
) -> Asiento:
    """A_FACT_EMIT_SERV_NAC_CON_RET.

    Debe: 430 (base+IVA−ret), 473 (ret)
    Haber: 705 (base), 477 (IVA)
    """
    iva = _pct(base_centimos, iva_pct)
    ret = _pct(base_centimos, retencion_pct)
    total_cliente = base_centimos + iva - ret
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("430", debe_centimos=total_cliente,
                  concepto_linea=f"Cliente {cliente_nif}"),
            Linea("705", haber_centimos=base_centimos),
            Linea("477", haber_centimos=iva),
            Linea("473", debe_centimos=ret),
        ],
        metadatos={
            "codigo": "A_FACT_EMIT_SERV_NAC_CON_RET",
            "cliente_nif": cliente_nif,
            "iva_pct": iva_pct,
            "retencion_pct": retencion_pct,
        },
    )


def fact_emit_serv_nac_sin_ret(
    *, indice, hash_previo, fecha, base_centimos, iva_pct,
    cliente_nif, concepto,
) -> Asiento:
    """A_FACT_EMIT_SERV_NAC_SIN_RET.

    Debe: 430 (base+IVA)
    Haber: 705 (base), 477 (IVA)
    """
    iva = _pct(base_centimos, iva_pct)
    total_cliente = base_centimos + iva
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("430", debe_centimos=total_cliente,
                  concepto_linea=f"Cliente {cliente_nif}"),
            Linea("705", haber_centimos=base_centimos),
            Linea("477", haber_centimos=iva),
        ],
        metadatos={
            "codigo": "A_FACT_EMIT_SERV_NAC_SIN_RET",
            "cliente_nif": cliente_nif,
            "iva_pct": iva_pct,
        },
    )


def fact_emit_serv_intra(
    *, indice, hash_previo, fecha, base_centimos,
    cliente_nif, concepto,
) -> Asiento:
    """A_FACT_EMIT_SERV_INTRA (intracomunitaria, ISP, sin IVA).

    Debe: 430 (base)
    Haber: 705 (base)
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("430", debe_centimos=base_centimos,
                  concepto_linea=f"Cliente {cliente_nif}"),
            Linea("705", haber_centimos=base_centimos),
        ],
        metadatos={
            "codigo": "A_FACT_EMIT_SERV_INTRA",
            "cliente_nif": cliente_nif,
            "tipo_operacion": "INTRA",
        },
    )


def fact_emit_serv_export(
    *, indice, hash_previo, fecha, base_centimos,
    cliente_nif, concepto,
) -> Asiento:
    """A_FACT_EMIT_SERV_EXPORT (exportación, exento, sin IVA).

    Debe: 430 (base)
    Haber: 705 (base)
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("430", debe_centimos=base_centimos,
                  concepto_linea=f"Cliente {cliente_nif}"),
            Linea("705", haber_centimos=base_centimos),
        ],
        metadatos={
            "codigo": "A_FACT_EMIT_SERV_EXPORT",
            "cliente_nif": cliente_nif,
            "tipo_operacion": "EXPORT",
        },
    )


# ─── Facturación emitida (mercaderías) ────────────────────────────

def fact_emit_merc_nac(
    *, indice, hash_previo, fecha, base_centimos, iva_pct,
    cliente_nif, concepto,
) -> Asiento:
    """A_FACT_EMIT_MERC_NAC.

    Debe: 430 (base+IVA)
    Haber: 700 (base), 477 (IVA)
    """
    iva = _pct(base_centimos, iva_pct)
    total_cliente = base_centimos + iva
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("430", debe_centimos=total_cliente,
                  concepto_linea=f"Cliente {cliente_nif}"),
            Linea("700", haber_centimos=base_centimos),
            Linea("477", haber_centimos=iva),
        ],
        metadatos={
            "codigo": "A_FACT_EMIT_MERC_NAC",
            "cliente_nif": cliente_nif,
            "iva_pct": iva_pct,
        },
    )


# ─── Factura rectificativa emitida ────────────────────────────────

def fact_rect_emit(
    *, indice, hash_previo, fecha, base_centimos, iva_pct,
    cliente_nif, concepto,
) -> Asiento:
    """A_FACT_RECT_EMIT (abono a cliente, reverso).

    Debe: 708 (base), 477 (IVA reverso)
    Haber: 430 (base+IVA)
    """
    iva = _pct(base_centimos, iva_pct)
    total_cliente = base_centimos + iva
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("708", debe_centimos=base_centimos),
            Linea("477", debe_centimos=iva),
            Linea("430", haber_centimos=total_cliente,
                  concepto_linea=f"Cliente {cliente_nif}"),
        ],
        metadatos={
            "codigo": "A_FACT_RECT_EMIT",
            "cliente_nif": cliente_nif,
            "iva_pct": iva_pct,
        },
    )


# ─── Facturación recibida (gasto) ─────────────────────────────────

def fact_rec_gasto_nac(
    *, indice, hash_previo, fecha, base_centimos, iva_pct,
    cuenta_gasto, proveedor_nif, concepto,
) -> Asiento:
    """A_FACT_REC_GASTO_NAC.

    Debe: {cuenta_gasto} (base), 472 (IVA)
    Haber: 400 (base+IVA)
    """
    iva = _pct(base_centimos, iva_pct)
    total_prov = base_centimos + iva
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea(cuenta_gasto, debe_centimos=base_centimos),
            Linea("472", debe_centimos=iva),
            Linea("400", haber_centimos=total_prov,
                  concepto_linea=f"Proveedor {proveedor_nif}"),
        ],
        metadatos={
            "codigo": "A_FACT_REC_GASTO_NAC",
            "cuenta_gasto": cuenta_gasto,
            "proveedor_nif": proveedor_nif,
            "iva_pct": iva_pct,
        },
    )


def fact_rec_gasto_profesional(
    *, indice, hash_previo, fecha, base_centimos, iva_pct, retencion_pct,
    cuenta_gasto, proveedor_nif, concepto,
) -> Asiento:
    """A_FACT_REC_GASTO_PROFESIONAL (con retención IRPF).

    Debe: {cuenta_gasto} (base), 472 (IVA)
    Haber: 4751 (ret), 410 (base+IVA−ret)
    """
    iva = _pct(base_centimos, iva_pct)
    ret = _pct(base_centimos, retencion_pct)
    total_prov = base_centimos + iva - ret
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea(cuenta_gasto, debe_centimos=base_centimos),
            Linea("472", debe_centimos=iva),
            Linea("4751", haber_centimos=ret),
            Linea("410", haber_centimos=total_prov,
                  concepto_linea=f"Proveedor {proveedor_nif}"),
        ],
        metadatos={
            "codigo": "A_FACT_REC_GASTO_PROFESIONAL",
            "cuenta_gasto": cuenta_gasto,
            "proveedor_nif": proveedor_nif,
            "iva_pct": iva_pct,
            "retencion_pct": retencion_pct,
        },
    )


def fact_rec_inmov(
    *, indice, hash_previo, fecha, base_centimos, iva_pct,
    cuenta_inmov, proveedor_nif, concepto,
) -> Asiento:
    """A_FACT_REC_INMOV (compra de inmovilizado).

    Debe: {cuenta_inmov} (base), 472 (IVA)
    Haber: 400 (base+IVA)
    """
    iva = _pct(base_centimos, iva_pct)
    total_prov = base_centimos + iva
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea(cuenta_inmov, debe_centimos=base_centimos),
            Linea("472", debe_centimos=iva),
            Linea("400", haber_centimos=total_prov,
                  concepto_linea=f"Proveedor {proveedor_nif}"),
        ],
        metadatos={
            "codigo": "A_FACT_REC_INMOV",
            "cuenta_inmov": cuenta_inmov,
            "proveedor_nif": proveedor_nif,
            "iva_pct": iva_pct,
        },
    )


def fact_rect_rec(
    *, indice, hash_previo, fecha, base_centimos, iva_pct,
    cuenta_gasto, proveedor_nif, concepto,
) -> Asiento:
    """A_FACT_RECT_REC (abono de proveedor, reverso).

    Debe: 400 (base+IVA)
    Haber: 608 (base), 472 (IVA)
    """
    iva = _pct(base_centimos, iva_pct)
    total_prov = base_centimos + iva
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("400", debe_centimos=total_prov,
                  concepto_linea=f"Proveedor {proveedor_nif}"),
            Linea("608", haber_centimos=base_centimos),
            Linea("472", haber_centimos=iva),
        ],
        metadatos={
            "codigo": "A_FACT_RECT_REC",
            "cuenta_gasto": cuenta_gasto,
            "proveedor_nif": proveedor_nif,
            "iva_pct": iva_pct,
        },
    )


# ─── Cobros y pagos ───────────────────────────────────────────────

def cobro_cliente_transf(
    *, indice, hash_previo, fecha, importe_centimos,
    cliente_nif, concepto,
) -> Asiento:
    """A_COBRO_CLIENTE_TRANSF.

    Debe: 572
    Haber: 430
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("572", debe_centimos=importe_centimos),
            Linea("430", haber_centimos=importe_centimos,
                  concepto_linea=f"Cliente {cliente_nif}"),
        ],
        metadatos={"codigo": "A_COBRO_CLIENTE_TRANSF", "cliente_nif": cliente_nif},
    )


def pago_proveedor_transf(
    *, indice, hash_previo, fecha, importe_centimos,
    proveedor_nif, concepto,
) -> Asiento:
    """A_PAGO_PROVEEDOR_TRANSF.

    Debe: 400
    Haber: 572
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("400", debe_centimos=importe_centimos,
                  concepto_linea=f"Proveedor {proveedor_nif}"),
            Linea("572", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_PAGO_PROVEEDOR_TRANSF", "proveedor_nif": proveedor_nif},
    )


def anticipo_cliente(
    *, indice, hash_previo, fecha, importe_centimos,
    cliente_nif, concepto,
) -> Asiento:
    """A_ANTICIPO_CLIENTE (cobro antes de factura).

    Debe: 572
    Haber: 438
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("572", debe_centimos=importe_centimos),
            Linea("438", haber_centimos=importe_centimos,
                  concepto_linea=f"Cliente {cliente_nif}"),
        ],
        metadatos={"codigo": "A_ANTICIPO_CLIENTE", "cliente_nif": cliente_nif},
    )


# ─── Nómina ──────────────────────────────────────────────────────

def nomina_mensual(
    *, indice, hash_previo, fecha, bruto_centimos,
    irpf_pct, ss_trabajador_pct, ss_empresa_pct,
    trabajador_nif, concepto,
) -> Asiento:
    """A_NOMINA_MENSUAL.

    Debe: 640 (bruto), 642 (SS empresa)
    Haber: 4751 (IRPF), 476 (SS trabajador + empresa), 572 (neto)
    """
    irpf = _pct(bruto_centimos, irpf_pct)
    ss_trab = _pct(bruto_centimos, ss_trabajador_pct)
    ss_emp = _pct(bruto_centimos, ss_empresa_pct)
    neto = bruto_centimos - irpf - ss_trab
    ss_total = ss_trab + ss_emp
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("640", debe_centimos=bruto_centimos),
            Linea("642", debe_centimos=ss_emp),
            Linea("4751", haber_centimos=irpf),
            Linea("476", haber_centimos=ss_total),
            Linea("572", haber_centimos=neto,
                  concepto_linea=f"Trabajador {trabajador_nif}"),
        ],
        metadatos={
            "codigo": "A_NOMINA_MENSUAL",
            "trabajador_nif": trabajador_nif,
            "irpf_pct": irpf_pct,
            "ss_trabajador_pct": ss_trabajador_pct,
            "ss_empresa_pct": ss_empresa_pct,
        },
    )


# ─── Dispatcher ──────────────────────────────────────────────────

ACTOS = {
    "A_FACT_EMIT_SERV_NAC_CON_RET": fact_emit_serv_nac_con_ret,
    "A_FACT_EMIT_SERV_NAC_SIN_RET": fact_emit_serv_nac_sin_ret,
    "A_FACT_EMIT_SERV_INTRA": fact_emit_serv_intra,
    "A_FACT_EMIT_SERV_EXPORT": fact_emit_serv_export,
    "A_FACT_EMIT_MERC_NAC": fact_emit_merc_nac,
    "A_FACT_RECT_EMIT": fact_rect_emit,
    "A_FACT_REC_GASTO_NAC": fact_rec_gasto_nac,
    "A_FACT_REC_GASTO_PROFESIONAL": fact_rec_gasto_profesional,
    "A_FACT_REC_INMOV": fact_rec_inmov,
    "A_FACT_RECT_REC": fact_rect_rec,
    "A_COBRO_CLIENTE_TRANSF": cobro_cliente_transf,
    "A_PAGO_PROVEEDOR_TRANSF": pago_proveedor_transf,
    "A_ANTICIPO_CLIENTE": anticipo_cliente,
    "A_NOMINA_MENSUAL": nomina_mensual,
}


def crear_acto(codigo: str, **params) -> Asiento:
    """Crea un asiento a partir de un código de acto y sus parámetros."""
    if codigo not in ACTOS:
        raise ValueError(
            f"Acto desconocido: {codigo}. "
            f"Disponibles: {sorted(ACTOS.keys())}"
        )
    return ACTOS[codigo](**params)
