# -*- coding: utf-8 -*-
"""Societarias avanzado: autocartera, dividendo a cuenta, aplicación resultado."""
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


def adquisicion_autocartera(
    *, indice, hash_previo, fecha, importe_centimos,
    concepto="Adquisición de acciones propias",
) -> Asiento:
    """A_ADQUISICION_AUTOCARTERA.

    Debe:  108
    Haber: 572
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("108", debe_centimos=importe_centimos),
            Linea("572", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_ADQUISICION_AUTOCARTERA"},
    )


def venta_autocartera(
    *, indice, hash_previo, fecha, precio_centimos, coste_centimos,
    concepto="Venta de acciones propias",
) -> Asiento:
    """A_VENTA_AUTOCARTERA.

    Debe:  572 (precio)
    Haber: 108 (coste), 1136 (resultado por autocartera)
    """
    diff = precio_centimos - coste_centimos
    lineas = [
        Linea("572", debe_centimos=precio_centimos),
        Linea("108", haber_centimos=coste_centimos),
    ]
    if diff > 0:
        lineas.append(Linea("1136", haber_centimos=diff))
    elif diff < 0:
        lineas.append(Linea("1136", debe_centimos=-diff))
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=lineas,
        metadatos={"codigo": "A_VENTA_AUTOCARTERA"},
    )


def dividendo_a_cuenta(
    *, indice, hash_previo, fecha, importe_centimos, retencion_pct,
    concepto="Dividendo a cuenta",
) -> Asiento:
    """A_DIVIDENDO_A_CUENTA.

    Debe:  129 (resultado)
    Haber: 526 (dividendo a pagar), 4751 (retención)
    """
    ret = _pct(importe_centimos, retencion_pct)
    lineas = [
        Linea("129", debe_centimos=importe_centimos),
        Linea("526", haber_centimos=importe_centimos - ret),
        Linea("4751", haber_centimos=ret),
    ]
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=lineas,
        metadatos={"codigo": "A_DIVIDENDO_A_CUENTA"},
    )


def aplicacion_resultado(
    *, indice, hash_previo, fecha, resultado_centimos,
    reserva_legal_centimos, reservas_voluntarias_centimos,
    concepto="Aplicación del resultado",
) -> Asiento:
    """A_APLICACION_RESULTADO.

    Si beneficio (positivo):
      Debe: 129
      Haber: 112 (reserva legal), 113 (reservas voluntarias), 526 (dividendos)
    Si pérdida (negativo): se imputa a remanente (121).
    """
    if resultado_centimos > 0:
        resto = resultado_centimos - reserva_legal_centimos - reservas_voluntarias_centimos
        lineas = [Linea("129", debe_centimos=resultado_centimos)]
        if reserva_legal_centimos > 0:
            lineas.append(Linea("112", haber_centimos=reserva_legal_centimos))
        if reservas_voluntarias_centimos > 0:
            lineas.append(Linea("113", haber_centimos=reservas_voluntarias_centimos))
        if resto > 0:
            lineas.append(Linea("121", haber_centimos=resto))
    else:
        lineas = [
            Linea("121", debe_centimos=-resultado_centimos),
            Linea("129", haber_centimos=-resultado_centimos),
        ]
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=lineas,
        metadatos={"codigo": "A_APLICACION_RESULTADO"},
    )


def prima_emision(
    *, indice, hash_previo, fecha, importe_centimos,
    concepto="Prima de emisión",
) -> Asiento:
    """A_PRIMA_EMISION.

    Debe:  572
    Haber: 110
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("572", debe_centimos=importe_centimos),
            Linea("110", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_PRIMA_EMISION"},
    )


def reserva_voluntaria(
    *, indice, hash_previo, fecha, importe_centimos,
    concepto="Reserva voluntaria",
) -> Asiento:
    """A_RESERVA_VOLUNTARIA.

    Debe:  129
    Haber: 113
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("129", debe_centimos=importe_centimos),
            Linea("113", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_RESERVA_VOLUNTARIA"},
    )


def transformacion_sociedad(
    *, indice, hash_previo, fecha, importe_centimos,
    concepto="Transformación de sociedad",
) -> Asiento:
    """A_TRANSFORMACION_SOCIEDAD (cambio de forma jurídica).

    Se reclasifica el capital según la nueva forma. Simplificado:
    Debe/Haber entre 100 y 100 (no cambia el importe total).
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("100", debe_centimos=importe_centimos),
            Linea("100", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_TRANSFORMACION_SOCIEDAD",
                   "tipo": "reclasificacion_sin_cambio_total"},
    )


ACTOS = {
    "A_ADQUISICION_AUTOCARTERA": adquisicion_autocartera,
    "A_VENTA_AUTOCARTERA": venta_autocartera,
    "A_DIVIDENDO_A_CUENTA": dividendo_a_cuenta,
    "A_APLICACION_RESULTADO": aplicacion_resultado,
    "A_PRIMA_EMISION": prima_emision,
    "A_RESERVA_VOLUNTARIA": reserva_voluntaria,
    "A_TRANSFORMACION_SOCIEDAD": transformacion_sociedad,
}


def crear_acto_societario_avanzado(codigo: str, **params) -> Asiento:
    if codigo not in ACTOS:
        raise ValueError(f"Acto societario avanzado desconocido: {codigo}")
    return ACTOS[codigo](**params)
