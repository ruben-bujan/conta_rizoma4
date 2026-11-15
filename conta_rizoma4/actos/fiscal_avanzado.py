# -*- coding: utf-8 -*-
"""Actos fiscales avanzados: modelos informativos, locales, sanciones, forales."""
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


# ─── Modelos informativos ─────────────────────────────────────

def modelo_347(
    *, indice, hash_previo, fecha, concepto="Declaración anual 347",
) -> Asiento:
    """A_MODELO_347 (operaciones con terceros). No genera asiento contable,
    pero se registra como acto."""
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[Linea("555", debe_centimos=0, haber_centimos=0)],
        metadatos={"codigo": "A_MODELO_347", "tipo": "informativo_sin_asiento"},
    )


def modelo_349(*, indice, hash_previo, fecha, concepto="Modelo 349") -> Asiento:
    """A_MODELO_349 (intracomunitarias). Informativo."""
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[Linea("555", debe_centimos=0, haber_centimos=0)],
        metadatos={"codigo": "A_MODELO_349", "tipo": "informativo_sin_asiento"},
    )


def modelo_369(*, indice, hash_previo, fecha, concepto="Modelo 369") -> Asiento:
    """A_MODELO_369 (ventanilla única OSS)."""
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[Linea("555", debe_centimos=0, haber_centimos=0)],
        metadatos={"codigo": "A_MODELO_369", "tipo": "informativo_sin_asiento"},
    )


# ─── Pagos fraccionados IRPF ─────────────────────────────────

def pago_fraccionado_130(
    *, indice, hash_previo, fecha, importe_centimos, concepto="Pago fraccionado 130",
) -> Asiento:
    """A_PAGO_FRACCIONADO_IRPF_130.

    Debe:  473
    Haber: 572
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("473", debe_centimos=importe_centimos),
            Linea("572", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_PAGO_FRACCIONADO_IRPF_130"},
    )


def pago_fraccionado_131(
    *, indice, hash_previo, fecha, importe_centimos, concepto="Pago fraccionado 131",
) -> Asiento:
    """A_PAGO_FRACCIONADO_IRPF_131 (estimación objetiva)."""
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("473", debe_centimos=importe_centimos),
            Linea("572", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_PAGO_FRACCIONADO_IRPF_131"},
    )


# ─── Impuestos locales ───────────────────────────────────────

def iae(*, indice, hash_previo, fecha, importe_centimos, concepto="IAE") -> Asiento:
    """A_IAE (Impuesto sobre Actividades Económicas).

    Debe:  631
    Haber: 572
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("631", debe_centimos=importe_centimos),
            Linea("572", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_IAE"},
    )


def ibi(*, indice, hash_previo, fecha, importe_centimos, concepto="IBI") -> Asiento:
    """A_IBI (Impuesto sobre Bienes Inmuebles).

    Debe:  631
    Haber: 572
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("631", debe_centimos=importe_centimos),
            Linea("572", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_IBI"},
    )


def itp_ajd(
    *, indice, hash_previo, fecha, base_centimos, tipo_pct,
    concepto="ITP/AJD",
) -> Asiento:
    """A_ITP_AJD (Transmisiones Patrimoniales y Actos Jurídicos Documentados).

    Debe:  631 (o 21x si es inmovilizado)
    Haber: 572
    """
    cuota = _pct(base_centimos, tipo_pct)
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("631", debe_centimos=cuota),
            Linea("572", haber_centimos=cuota),
        ],
        metadatos={"codigo": "A_ITP_AJD", "tipo_pct": tipo_pct},
    )


# ─── Sanciones y regularizaciones ───────────────────────────

def sancion_tributaria(
    *, indice, hash_previo, fecha, importe_centimos,
    concepto="Sanción tributaria",
) -> Asiento:
    """A_SANCION_TRIBUTARIA.

    Debe:  678
    Haber: 4752 (o 572)
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("678", debe_centimos=importe_centimos),
            Linea("4752", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_SANCION_TRIBUTARIA"},
    )


def interes_demora(
    *, indice, hash_previo, fecha, importe_centimos,
    concepto="Intereses de demora",
) -> Asiento:
    """A_INTERES_DEMORA.

    Debe:  669
    Haber: 4752
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("669", debe_centimos=importe_centimos),
            Linea("4752", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_INTERES_DEMORA"},
    )


def regularizacion_iva(
    *, indice, hash_previo, fecha, importe_centimos,
    concepto="Regularización IVA",
) -> Asiento:
    """A_REGULARIZACION_IVA (diferencia con Hacienda).

    Debe:  477
    Haber: 472, 4750 / 4700
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("477", debe_centimos=importe_centimos),
            Linea("4750", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_REGULARIZACION_IVA"},
    )


def regularizacion_irpf(
    *, indice, hash_previo, fecha, importe_centimos,
    concepto="Regularización IRPF",
) -> Asiento:
    """A_REGULARIZACION_IRPF.

    Debe:  4751
    Haber: 572
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("4751", debe_centimos=importe_centimos),
            Linea("572", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_REGULARIZACION_IRPF"},
    )


def regularizacion_is(
    *, indice, hash_previo, fecha, importe_centimos,
    concepto="Regularización IS",
) -> Asiento:
    """A_REGULARIZACION_IS.

    Debe:  6300
    Haber: 4752
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("6300", debe_centimos=importe_centimos),
            Linea("4752", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_REGULARIZACION_IS"},
    )


# ─── Forales (País Vasco, Navarra, Canarias) ────────────────

def iva_foral(
    *, indice, hash_previo, fecha, iva_repercutido_centimos,
    iva_soportado_centimos, concepto="Liquidación IVA foral",
) -> Asiento:
    """A_IVA_FORAL (País Vasco, Navarra). Mismo esquema que 303.

    Debe:  477
    Haber: 472, 4750
    """
    diff = iva_repercutido_centimos - iva_soportado_centimos
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("477", debe_centimos=iva_repercutido_centimos),
            Linea("472", haber_centimos=iva_soportado_centimos),
            Linea("4750", haber_centimos=diff),
        ],
        metadatos={"codigo": "A_IVA_FORAL"},
    )


def igic_canarias(
    *, indice, hash_previo, fecha, igic_repercutido_centimos,
    igic_soportado_centimos, concepto="Liquidación IGIC",
) -> Asiento:
    """A_IGIC_CANARIAS (Impuesto General Indirecto de Canarias).

    Debe:  477
    Haber: 472, 4750
    """
    diff = igic_repercutido_centimos - igic_soportado_centimos
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("477", debe_centimos=igic_repercutido_centimos),
            Linea("472", haber_centimos=igic_soportado_centimos),
            Linea("4750", haber_centimos=diff),
        ],
        metadatos={"codigo": "A_IGIC_CANARIAS"},
    )


# ─── Patrimonio y bienes en el extranjero ──────────────────

def modelo_720(
    *, indice, hash_previo, fecha, concepto="Modelo 720",
) -> Asiento:
    """A_MODELO_720 (bienes en el extranjero). Informativo."""
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[Linea("555", debe_centimos=0, haber_centimos=0)],
        metadatos={"codigo": "A_MODELO_720", "tipo": "informativo_sin_asiento"},
    )


def modelo_721(
    *, indice, hash_previo, fecha, concepto="Modelo 721",
) -> Asiento:
    """A_MODELO_721 (criptomonedas). Informativo."""
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[Linea("555", debe_centimos=0, haber_centimos=0)],
        metadatos={"codigo": "A_MODELO_721", "tipo": "informativo_sin_asiento"},
    )


def modelo_714(
    *, indice, hash_previo, fecha, concepto="Modelo 714",
) -> Asiento:
    """A_MODELO_714 (Impuesto sobre el Patrimonio). Informativo."""
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[Linea("555", debe_centimos=0, haber_centimos=0)],
        metadatos={"codigo": "A_MODELO_714", "tipo": "informativo_sin_asiento"},
    )


# ─── Impuestos especiales ────────────────────────────────────

def impuesto_primas_seguros(
    *, indice, hash_previo, fecha, base_centimos, tipo_pct=8,
    concepto="Impuesto sobre primas de seguros",
) -> Asiento:
    """A_IMPUESTO_PRIMAS_SEGUROS.

    Debe:  625 (o cuenta de gasto)
    Haber: 4752
    """
    cuota = _pct(base_centimos, tipo_pct)
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("625", debe_centimos=cuota),
            Linea("4752", haber_centimos=cuota),
        ],
        metadatos={"codigo": "A_IMPUESTO_PRIMAS_SEGUROS", "tipo_pct": tipo_pct},
    )


def impuesto_actividades_juego(
    *, indice, hash_previo, fecha, importe_centimos,
    concepto="Impuesto sobre actividades de juego",
) -> Asiento:
    """A_IMPUESTO_ACTIVIDADES_JUEGO.

    Debe:  631
    Haber: 4752
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("631", debe_centimos=importe_centimos),
            Linea("4752", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_IMPUESTO_ACTIVIDADES_JUEGO"},
    )


def impuesto_hidrocarburos(
    *, indice, hash_previo, fecha, importe_centimos,
    concepto="Impuesto sobre hidrocarburos",
) -> Asiento:
    """A_IMPUESTO_HIDROCARBUROS.

    Debe:  628
    Haber: 4752
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("628", debe_centimos=importe_centimos),
            Linea("4752", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_IMPUESTO_HIDROCARBUROS"},
    )


def impuesto_alcohol(
    *, indice, hash_previo, fecha, importe_centimos,
    concepto="Impuesto sobre el alcohol",
) -> Asiento:
    """A_IMPUESTO_ALCOHOL.

    Debe:  631
    Haber: 4752
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("631", debe_centimos=importe_centimos),
            Linea("4752", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_IMPUESTO_ALCOHOL"},
    )


def impuesto_tabaco(
    *, indice, hash_previo, fecha, importe_centimos,
    concepto="Impuesto sobre el tabaco",
) -> Asiento:
    """A_IMPUESTO_TABACO.

    Debe:  631
    Haber: 4752
    """
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("631", debe_centimos=importe_centimos),
            Linea("4752", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_IMPUESTO_TABACO"},
    )


ACTOS = {
    "A_MODELO_347": modelo_347,
    "A_MODELO_349": modelo_349,
    "A_MODELO_369": modelo_369,
    "A_PAGO_FRACCIONADO_IRPF_130": pago_fraccionado_130,
    "A_PAGO_FRACCIONADO_IRPF_131": pago_fraccionado_131,
    "A_IAE": iae,
    "A_IBI": ibi,
    "A_ITP_AJD": itp_ajd,
    "A_SANCION_TRIBUTARIA": sancion_tributaria,
    "A_INTERES_DEMORA": interes_demora,
    "A_REGULARIZACION_IVA": regularizacion_iva,
    "A_REGULARIZACION_IRPF": regularizacion_irpf,
    "A_REGULARIZACION_IS": regularizacion_is,
    "A_IVA_FORAL": iva_foral,
    "A_IGIC_CANARIAS": igic_canarias,
    "A_MODELO_720": modelo_720,
    "A_MODELO_721": modelo_721,
    "A_MODELO_714": modelo_714,
    "A_IMPUESTO_PRIMAS_SEGUROS": impuesto_primas_seguros,
    "A_IMPUESTO_ACTIVIDADES_JUEGO": impuesto_actividades_juego,
    "A_IMPUESTO_HIDROCARBUROS": impuesto_hidrocarburos,
    "A_IMPUESTO_ALCOHOL": impuesto_alcohol,
    "A_IMPUESTO_TABACO": impuesto_tabaco,
}


def crear_acto_fiscal_avanzado(codigo: str, **params) -> Asiento:
    if codigo not in ACTOS:
        raise ValueError(f"Acto fiscal avanzado desconocido: {codigo}")
    return ACTOS[codigo](**params)
