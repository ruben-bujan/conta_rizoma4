# -*- coding: utf-8 -*-
"""Actos fiscales: liquidaciones y resúmenes de IVA, IRPF, IS."""
from __future__ import annotations

from datetime import date
from typing import Any, Optional

from ..partida_doble.modelo import Asiento, Linea
from ..partida_doble.creacion import crear_asiento


def _asiento(*, indice, hash_previo, fecha, concepto, lineas, metadatos=None):
    return crear_asiento(
        indice=indice, fecha=fecha, concepto=concepto,
        lineas=lineas, hash_previo=hash_previo, metadatos=metadatos,
    )


# ─── IVA: liquidaciones trimestrales (303) ─────────────────────────

def liq_iva_trim_303_ingresar(
    *, indice, hash_previo, fecha, iva_repercutido_centimos,
    iva_soportado_centimos, concepto,
) -> Asiento:
    """A_LIQ_IVA_TRIM_303_INGRESAR.

    Debe:  477 = IVA repercutido
    Haber: 472 = IVA soportado, 4750 = a ingresar
    """
    a_ingresar = iva_repercutido_centimos - iva_soportado_centimos
    if a_ingresar <= 0:
        raise ValueError(
            f"a ingresar debe ser > 0 (es {a_ingresar}); "
            f"usa liq_iva_trim_303_devolver o compensar"
        )
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("477", debe_centimos=iva_repercutido_centimos),
            Linea("472", haber_centimos=iva_soportado_centimos),
            Linea("4750", haber_centimos=a_ingresar),
        ],
        metadatos={"codigo": "A_LIQ_IVA_TRIM_303_INGRESAR"},
    )


def liq_iva_trim_303_devolver(
    *, indice, hash_previo, fecha, iva_repercutido_centimos,
    iva_soportado_centimos, concepto,
) -> Asiento:
    """A_LIQ_IVA_TRIM_303_DEVOLVER.

    Debe:  477 = IVA repercutido, 4700 = a devolver
    Haber: 472 = IVA soportado
    """
    a_devolver = iva_soportado_centimos - iva_repercutido_centimos
    if a_devolver <= 0:
        raise ValueError(
            f"a devolver debe ser > 0 (es {a_devolver}); "
            f"usa liq_iva_trim_303_ingresar"
        )
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("477", debe_centimos=iva_repercutido_centimos),
            Linea("4700", debe_centimos=a_devolver),
            Linea("472", haber_centimos=iva_soportado_centimos),
        ],
        metadatos={"codigo": "A_LIQ_IVA_TRIM_303_DEVOLVER"},
    )


def liq_iva_trim_303_compensar(
    *, indice, hash_previo, fecha, iva_repercutido_centimos,
    iva_soportado_centimos, concepto,
) -> Asiento:
    """A_LIQ_IVA_TRIM_303_COMPENSAR.

    Debe:  477
    Haber: 472, 4700 = a compensar (queda a favor para próximos trimestres)
    """
    a_compensar = iva_soportado_centimos - iva_repercutido_centimos
    if a_compensar <= 0:
        raise ValueError(f"a compensar debe ser > 0 (es {a_compensar})")
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("477", debe_centimos=iva_repercutido_centimos),
            Linea("4700", debe_centimos=a_compensar),
            Linea("472", haber_centimos=iva_soportado_centimos),
        ],
        metadatos={"codigo": "A_LIQ_IVA_TRIM_303_COMPENSAR"},
    )


# ─── IVA: resumen anual (390) ────────────────────────────────────

def resumen_anual_iva_390(
    *, indice, hash_previo, fecha, iva_repercutido_centimos,
    iva_soportado_centimos, concepto,
) -> Asiento:
    """A_RESUMEN_ANUAL_IVA_390.

    Mismo asiento que el 4T de 303 (no genera movimiento nuevo, pero
    consolida el año). Se contabiliza si hay diferencias con el 4T.
    """
    diff = iva_repercutido_centimos - iva_soportado_centimos
    if diff == 0:
        raise ValueError("sin diferencias: no hay asiento de resumen 390")
    if diff > 0:
        return _asiento(
            indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
            lineas=[
                Linea("477", debe_centimos=iva_repercutido_centimos),
                Linea("472", haber_centimos=iva_soportado_centimos),
                Linea("4750", haber_centimos=diff),
            ],
            metadatos={"codigo": "A_RESUMEN_ANUAL_IVA_390"},
        )
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("477", debe_centimos=iva_repercutido_centimos),
            Linea("4700", debe_centimos=-diff),
            Linea("472", haber_centimos=iva_soportado_centimos),
        ],
        metadatos={"codigo": "A_RESUMEN_ANUAL_IVA_390"},
    )


# ─── IRPF: liquidaciones trimestrales ─────────────────────────────

def liq_irpf_trim_111(
    *, indice, hash_previo, fecha, retenciones_centimos, concepto,
) -> Asiento:
    """A_LIQ_IRPF_TRIM_111 (retenciones trabajo + profesionales).

    Debe:  4751 = retenciones
    Haber: 572 = a ingresar
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("4751", debe_centimos=retenciones_centimos),
            Linea("572", haber_centimos=retenciones_centimos),
        ],
        metadatos={"codigo": "A_LIQ_IRPF_TRIM_111"},
    )


def liq_irpf_trim_115(
    *, indice, hash_previo, fecha, retenciones_centimos, concepto,
) -> Asiento:
    """A_LIQ_IRPF_TRIM_115 (retenciones alquileres)."""
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("4751", debe_centimos=retenciones_centimos),
            Linea("572", haber_centimos=retenciones_centimos),
        ],
        metadatos={"codigo": "A_LIQ_IRPF_TRIM_115"},
    )


def liq_irpf_trim_123(
    *, indice, hash_previo, fecha, retenciones_centimos, concepto,
) -> Asiento:
    """A_LIQ_IRPF_TRIM_123 (retenciones dividendos)."""
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("4751", debe_centimos=retenciones_centimos),
            Linea("572", haber_centimos=retenciones_centimos),
        ],
        metadatos={"codigo": "A_LIQ_IRPF_TRIM_123"},
    )


# ─── IRPF: resúmenes anuales ─────────────────────────────────────

def resumen_anual_190(
    *, indice, hash_previo, fecha, retenciones_centimos, concepto,
) -> Asiento:
    """A_RESUMEN_ANUAL_190 (resumen de 111)."""
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("4751", debe_centimos=retenciones_centimos),
            Linea("572", haber_centimos=retenciones_centimos),
        ],
        metadatos={"codigo": "A_RESUMEN_ANUAL_190"},
    )


def resumen_anual_180(
    *, indice, hash_previo, fecha, retenciones_centimos, concepto,
) -> Asiento:
    """A_RESUMEN_ANUAL_180 (resumen de 115)."""
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("4751", debe_centimos=retenciones_centimos),
            Linea("572", haber_centimos=retenciones_centimos),
        ],
        metadatos={"codigo": "A_RESUMEN_ANUAL_180"},
    )


def resumen_anual_193(
    *, indice, hash_previo, fecha, retenciones_centimos, concepto,
) -> Asiento:
    """A_RESUMEN_ANUAL_193 (resumen de 123)."""
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("4751", debe_centimos=retenciones_centimos),
            Linea("572", haber_centimos=retenciones_centimos),
        ],
        metadatos={"codigo": "A_RESUMEN_ANUAL_193"},
    )


# ─── Impuesto de Sociedades (200) ────────────────────────────────

def liq_is_anual_200(
    *, indice, hash_previo, fecha, base_imponible_centimos,
    tipo_pct, concepto,
) -> Asiento:
    """A_LIQ_IS_ANUAL_200.

    Debe:  6300 = impuesto corriente
    Haber: 4752 = HP acreedora por IS
    """
    cuota = int(round(base_imponible_centimos * tipo_pct / 100))
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("6300", debe_centimos=cuota),
            Linea("4752", haber_centimos=cuota),
        ],
        metadatos={"codigo": "A_LIQ_IS_ANUAL_200", "tipo_pct": tipo_pct},
    )


# ─── Dispatcher ──────────────────────────────────────────────────

ACTOS = {
    "A_LIQ_IVA_TRIM_303_INGRESAR": liq_iva_trim_303_ingresar,
    "A_LIQ_IVA_TRIM_303_DEVOLVER": liq_iva_trim_303_devolver,
    "A_LIQ_IVA_TRIM_303_COMPENSAR": liq_iva_trim_303_compensar,
    "A_RESUMEN_ANUAL_IVA_390": resumen_anual_iva_390,
    "A_LIQ_IRPF_TRIM_111": liq_irpf_trim_111,
    "A_LIQ_IRPF_TRIM_115": liq_irpf_trim_115,
    "A_LIQ_IRPF_TRIM_123": liq_irpf_trim_123,
    "A_RESUMEN_ANUAL_190": resumen_anual_190,
    "A_RESUMEN_ANUAL_180": resumen_anual_180,
    "A_RESUMEN_ANUAL_193": resumen_anual_193,
    "A_LIQ_IS_ANUAL_200": liq_is_anual_200,
}


def crear_acto_fiscal(codigo: str, **params) -> Asiento:
    if codigo not in ACTOS:
        raise ValueError(f"Acto fiscal desconocido: {codigo}")
    return ACTOS[codigo](**params)
