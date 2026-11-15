# -*- coding: utf-8 -*-
"""Operaciones especiales: combinaciones de negocios, consolidación,
derivados, confirming, pagos en acciones, operaciones con el grupo."""
from __future__ import annotations

from ..partida_doble.modelo import Asiento, Linea
from ..partida_doble.creacion import crear_asiento


def _asiento(*, indice, hash_previo, fecha, concepto, lineas, metadatos=None):
    return crear_asiento(
        indice=indice, fecha=fecha, concepto=concepto,
        lineas=lineas, hash_previo=hash_previo, metadatos=metadatos,
    )


# ─── Combinaciones de negocios (NRV 12) ────────────────────

def fusion_por_absorcion(
    *, indice, hash_previo, fecha, valor_razonable_centimos,
    capital_emitido_centimos, prima_centimos,
    concepto="Fusión por absorción",
) -> Asiento:
    """A_FUSION_POR_ABSORCION (la absorbente incorpora el patrimonio).

    Debe:  Activos recibidos (simplificado: 21x)
    Haber: 100 (capital emitido), 110 (prima), 553 (socios cuenta fusión)
    """
    resto = valor_razonable_centimos - capital_emitido_centimos - prima_centimos
    lineas = [
        Linea("21x", debe_centimos=valor_razonable_centimos),
        Linea("100", haber_centimos=capital_emitido_centimos),
        Linea("110", haber_centimos=prima_centimos),
    ]
    if resto > 0:
        lineas.append(Linea("553", haber_centimos=resto))
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=lineas,
        metadatos={"codigo": "A_FUSION_POR_ABSORCION"},
    )


def escision_parcial(
    *, indice, hash_previo, fecha, valor_escindido_centimos,
    cuenta_inmov, concepto="Escisión parcial",
) -> Asiento:
    """A_ESCISION_PARCIAL (se segrega una rama de actividad)."""
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("553", debe_centimos=valor_escindido_centimos),
            Linea(cuenta_inmov, haber_centimos=valor_escindido_centimos),
        ],
        metadatos={"codigo": "A_ESCISION_PARCIAL"},
    )


def fondo_de_comercio(
    *, indice, hash_previo, fecha, importe_centimos,
    concepto="Fondo de comercio (goodwill)",
) -> Asiento:
    """A_FONDO_DE_COMERCIO (exceso del precio sobre el valor razonable)."""
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("204", debe_centimos=importe_centimos),
            Linea("553", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_FONDO_DE_COMERCIO"},
    )


# ─── Consolidación (grupos de sociedades) ──────────────────

def eliminacion_intragrupo(
    *, indice, hash_previo, fecha, importe_centimos,
    cuenta_origen, cuenta_destino, concepto="Eliminación intragrupo",
) -> Asiento:
    """A_ELIMINACION_INTRAGRUPO (eliminar operaciones entre empresas del grupo)."""
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea(cuenta_destino, debe_centimos=importe_centimos),
            Linea(cuenta_origen, haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_ELIMINACION_INTRAGRUPO"},
    )


def atribucion_socios_minoritarios(
    *, indice, hash_previo, fecha, importe_centimos,
    concepto="Atribución a socios minoritarios",
) -> Asiento:
    """A_ATRIBUCION_SOCIOS_MINORITARIOS."""
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("129", debe_centimos=importe_centimos),
            Linea("118", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_ATRIBUCION_SOCIOS_MINORITARIOS"},
    )


# ─── Derivados y coberturas (NRV 6) ───────────────────────

def compra_derivado(
    *, indice, hash_previo, fecha, prima_centimos,
    cuenta_derivado="5590", concepto="Compra de derivado",
) -> Asiento:
    """A_COMPRA_DERIVADO (opción, futuro, swap)."""
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea(cuenta_derivado, debe_centimos=prima_centimos),
            Linea("572", haber_centimos=prima_centimos),
        ],
        metadatos={"codigo": "A_COMPRA_DERIVADO"},
    )


def valoracion_derivado_favorable(
    *, indice, hash_previo, fecha, importe_centimos,
    cuenta_derivado="5590", concepto="Valoración favorable derivado",
) -> Asiento:
    """A_VALORACION_DERIVADO_FAVORABLE."""
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea(cuenta_derivado, debe_centimos=importe_centimos),
            Linea("7632", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_VALORACION_DERIVADO_FAVORABLE"},
    )


def valoracion_derivado_desfavorable(
    *, indice, hash_previo, fecha, importe_centimos,
    cuenta_derivado="5590", concepto="Valoración desfavorable derivado",
) -> Asiento:
    """A_VALORACION_DERIVADO_DESFAVORABLE."""
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("6632", debe_centimos=importe_centimos),
            Linea(cuenta_derivado, haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_VALORACION_DERIVADO_DESFAVORABLE"},
    )


# ─── Confirming, factoring, descuento ─────────────────────

def confirming_proveedor(
    *, indice, hash_previo, fecha, importe_centimos,
    concepto="Confirming a proveedor",
) -> Asiento:
    """A_CONFIRMING_PROVEEDOR (el banco paga al proveedor, la empresa al banco)."""
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("400", debe_centimos=importe_centimos),
            Linea("5208", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_CONFIRMING_PROVEEDOR"},
    )


def factoring_cliente(
    *, indice, hash_previo, fecha, importe_centimos, comision_centimos,
    concepto="Factoring de cliente",
) -> Asiento:
    """A_FACTORING_CLIENTE (cesión de créditos al banco)."""
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("572", debe_centimos=importe_centimos - comision_centimos),
            Linea("626", debe_centimos=comision_centimos),
            Linea("430", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_FACTORING_CLIENTE"},
    )


def descuento_efectos(
    *, indice, hash_previo, fecha, nominal_centimos,
    intereses_centimos, concepto="Descuento de efectos",
) -> Asiento:
    """A_DESCUENTO_EFECTOS (descuento bancario de letras/pagarés)."""
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("572", debe_centimos=nominal_centimos - intereses_centimos),
            Linea("626", debe_centimos=intereses_centimos),
            Linea("431", haber_centimos=nominal_centimos),
        ],
        metadatos={"codigo": "A_DESCUENTO_EFECTOS"},
    )


# ─── Pagos basados en acciones (NRV 20) ────────────────────

def pago_basado_acciones(
    *, indice, hash_previo, fecha, importe_centimos,
    concepto="Pago basado en acciones (equity-settled)",
) -> Asiento:
    """A_PAGO_BASADO_ACCIONES."""
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("640", debe_centimos=importe_centimos),
            Linea("111", haber_centimos=importe_centimos),
        ],
        metadatos={"codigo": "A_PAGO_BASADO_ACCIONES"},
    )


# ─── Operaciones entre empresas del grupo (NRV 14) ────────

def venta_a_empresa_grupo(
    *, indice, hash_previo, fecha, base_centimos, iva_pct,
    empresa_nif, concepto="Venta a empresa del grupo",
) -> Asiento:
    """A_VENTA_A_EMPRESA_GRUPO."""
    iva = int(round(base_centimos * iva_pct / 100))
    return _asiento(
        indice=indice, hash_previo=hash_previo, fecha=fecha, concepto=concepto,
        lineas=[
            Linea("430", debe_centimos=base_centimos + iva,
                  concepto_linea=f"Empresa grupo {empresa_nif}"),
            Linea("705", haber_centimos=base_centimos),
            Linea("477", haber_centimos=iva),
        ],
        metadatos={"codigo": "A_VENTA_A_EMPRESA_GRUPO"},
    )


ACTOS = {
    "A_FUSION_POR_ABSORCION": fusion_por_absorcion,
    "A_ESCISION_PARCIAL": escision_parcial,
    "A_FONDO_DE_COMERCIO": fondo_de_comercio,
    "A_ELIMINACION_INTRAGRUPO": eliminacion_intragrupo,
    "A_ATRIBUCION_SOCIOS_MINORITARIOS": atribucion_socios_minoritarios,
    "A_COMPRA_DERIVADO": compra_derivado,
    "A_VALORACION_DERIVADO_FAVORABLE": valoracion_derivado_favorable,
    "A_VALORACION_DERIVADO_DESFAVORABLE": valoracion_derivado_desfavorable,
    "A_CONFIRMING_PROVEEDOR": confirming_proveedor,
    "A_FACTORING_CLIENTE": factoring_cliente,
    "A_DESCUENTO_EFECTOS": descuento_efectos,
    "A_PAGO_BASADO_ACCIONES": pago_basado_acciones,
    "A_VENTA_A_EMPRESA_GRUPO": venta_a_empresa_grupo,
}


def crear_acto_especial(codigo: str, **params) -> Asiento:
    if codigo not in ACTOS:
        raise ValueError(f"Acto especial desconocido: {codigo}")
    return ACTOS[codigo](**params)
