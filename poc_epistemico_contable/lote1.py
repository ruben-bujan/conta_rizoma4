"""Primer lote de migración de actos económicos puros.

Incluye facturas, cobros y pagos básicos. Los generadores producen hechos y
líneas epistemológicas mínimas; no persisten ni crean adaptadores PostgreSQL.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Any


@dataclass(frozen=True)
class ResultadoLote1:
    codigo: str
    tipo_hecho: str
    lineas: tuple[tuple[str, int, int], ...]
    parametros: dict[str, Any]


def _linea(cuenta: str, debe: int = 0, haber: int = 0) -> tuple[str, int, int]:
    return (cuenta, debe, haber)


def factura_emitida_sin_retencion(*, base_centimos: int, iva_pct: float,
                                   cliente_nif: str = "",
                                   concepto: str = "Factura emitida") -> ResultadoLote1:
    if base_centimos < 0:
        raise ValueError("base_centimos no puede ser negativo")
    if iva_pct < 0:
        raise ValueError("iva_pct no puede ser negativo")
    iva = int(round(base_centimos * iva_pct / 100))
    total = base_centimos + iva
    return ResultadoLote1(
        "A_FACT_EMIT_SERV_NAC_SIN_RET",
        "FACTURA_EMITIDA",
        (_linea("430", total, 0), _linea("705", 0, base_centimos), _linea("477", 0, iva)),
        {"cliente_nif": cliente_nif, "concepto": concepto, "iva_pct": iva_pct},
    )


def factura_emitida_con_retencion(*, base_centimos: int, iva_pct: float,
                                  retencion_pct: float,
                                  cliente_nif: str = "",
                                  concepto: str = "Factura emitida") -> ResultadoLote1:
    if base_centimos < 0:
        raise ValueError("base_centimos no puede ser negativo")
    if iva_pct < 0 or retencion_pct < 0:
        raise ValueError("Los porcentajes no pueden ser negativos")
    iva = int(round(base_centimos * iva_pct / 100))
    retencion = int(round(base_centimos * retencion_pct / 100))
    total = base_centimos + iva - retencion
    if total < 0:
        raise ValueError("El importe pendiente no puede ser negativo")
    return ResultadoLote1(
        "A_FACT_EMIT_SERV_NAC_CON_RET",
        "FACTURA_EMITIDA",
        (
            _linea("430", total, 0),
            _linea("705", 0, base_centimos),
            _linea("477", 0, iva),
            _linea("473", retencion, 0),
        ),
        {"cliente_nif": cliente_nif, "concepto": concepto,
         "iva_pct": iva_pct, "retencion_pct": retencion_pct},
    )


def factura_recibida_gasto(*, base_centimos: int, iva_pct: float,
                           cuenta_gasto: str,
                           proveedor_nif: str = "",
                           concepto: str = "Factura recibida") -> ResultadoLote1:
    if base_centimos < 0:
        raise ValueError("base_centimos no puede ser negativo")
    if not cuenta_gasto:
        raise ValueError("cuenta_gasto es obligatoria")
    if iva_pct < 0:
        raise ValueError("iva_pct no puede ser negativo")
    iva = int(round(base_centimos * iva_pct / 100))
    total = base_centimos + iva
    return ResultadoLote1(
        "A_FACT_REC_GASTO_NAC",
        "FACTURA_RECIBIDA",
        (_linea(cuenta_gasto, base_centimos, 0),
         _linea("472", iva, 0),
         _linea("400", 0, total)),
        {"proveedor_nif": proveedor_nif, "concepto": concepto,
         "cuenta_gasto": cuenta_gasto, "iva_pct": iva_pct},
    )


def cobro_cliente(*, importe_centimos: int,
                  cliente_nif: str = "",
                  concepto: str = "Cobro de cliente") -> ResultadoLote1:
    if importe_centimos < 0:
        raise ValueError("importe_centimos no puede ser negativo")
    return ResultadoLote1(
        "A_COBRO_CLIENTE_TRANSF",
        "COBRO",
        (_linea("572", importe_centimos, 0), _linea("430", 0, importe_centimos)),
        {"cliente_nif": cliente_nif, "concepto": concepto},
    )


def pago_proveedor(*, importe_centimos: int,
                   proveedor_nif: str = "",
                   concepto: str = "Pago a proveedor") -> ResultadoLote1:
    if importe_centimos < 0:
        raise ValueError("importe_centimos no puede ser negativo")
    return ResultadoLote1(
        "A_PAGO_PROVEEDOR_TRANSF",
        "PAGO",
        (_linea("400", importe_centimos, 0), _linea("572", 0, importe_centimos)),
        {"proveedor_nif": proveedor_nif, "concepto": concepto},
    )


def anticipo_cliente(*, importe_centimos: int,
                     cliente_nif: str = "",
                     concepto: str = "Anticipo de cliente") -> ResultadoLote1:
    if importe_centimos < 0:
        raise ValueError("importe_centimos no puede ser negativo")
    return ResultadoLote1(
        "A_ANTICIPO_CLIENTE",
        "ANTICIPO",
        (_linea("572", importe_centimos, 0), _linea("438", 0, importe_centimos)),
        {"cliente_nif": cliente_nif, "concepto": concepto},
    )


REGISTRO_LOTE1: dict[str, Callable[..., ResultadoLote1]] = {
    "A_FACT_EMIT_SERV_NAC_SIN_RET": factura_emitida_sin_retencion,
    "A_FACT_EMIT_SERV_NAC_CON_RET": factura_emitida_con_retencion,
    "A_FACT_REC_GASTO_NAC": factura_recibida_gasto,
    "A_COBRO_CLIENTE_TRANSF": cobro_cliente,
    "A_PAGO_PROVEEDOR_TRANSF": pago_proveedor,
    "A_ANTICIPO_CLIENTE": anticipo_cliente,
}


def generar_lote1(codigo: str, **parametros: Any) -> ResultadoLote1:
    if codigo not in REGISTRO_LOTE1:
        raise ValueError(f"Código no incluido en el primer lote: {codigo}")
    return REGISTRO_LOTE1[codigo](**parametros)
