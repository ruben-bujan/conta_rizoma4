"""Casos de uso básicos de facturación, independientes de infraestructura."""
from __future__ import annotations

from datetime import datetime
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from ..entidades.economicas import (
    EjercicioContable,
    MovimientoEconomico,
    Tercero,
)
from ..entidades.contables import Linea, RepresentacionContable


class FacturaError(ValueError):
    pass


@dataclass(frozen=True)
class ResultadoFactura:
    tercero: Tercero
    movimiento: MovimientoEconomico
    representacion: RepresentacionContable


def calcular_iva(base_centimos: int, iva_pct: float) -> int:
    if not isinstance(base_centimos, int) or isinstance(base_centimos, bool) or base_centimos < 0:
        raise FacturaError("base_centimos no puede ser negativo")
    try:
        porcentaje = Decimal(str(iva_pct))
    except (InvalidOperation, ValueError):
        raise FacturaError("iva_pct no es válido") from None
    if not porcentaje.is_finite() or porcentaje < 0:
        raise FacturaError("iva_pct no puede ser negativo")
    return int((Decimal(base_centimos) * porcentaje / Decimal(100)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _validar_factura(*, entidad_id: str, tercero: Tercero, ejercicio: EjercicioContable,
                     fecha: datetime, numero_factura: str, representacion_id: str,
                     hecho_ids: tuple[str, ...], interpretacion_id: str,
                     decision_id: str, criterio_ids: tuple[str, ...]) -> None:
    if tercero.tipo not in ("JURIDICA", "FISICA"):
        raise FacturaError("Tipo de tercero no válido")
    if not tercero.activo:
        raise FacturaError("El tercero está inactivo")
    if entidad_id != ejercicio.entidad_id:
        raise FacturaError("La entidad no coincide con el ejercicio")
    if not ejercicio.permite_registro:
        raise FacturaError("El ejercicio no está abierto")
    if not ejercicio.inicio <= fecha <= ejercicio.fin:
        raise FacturaError("La factura está fuera del ejercicio")
    if not numero_factura or not numero_factura.strip():
        raise FacturaError("El número de factura es obligatorio")
    if not representacion_id.strip() or not interpretacion_id.strip() or not decision_id.strip():
        raise FacturaError("La factura requiere IDs de representación, interpretación y decisión")
    if not hecho_ids or any(not x.strip() for x in hecho_ids):
        raise FacturaError("La factura requiere al menos un hecho identificado")
    if not criterio_ids or any(not x.strip() for x in criterio_ids):
        raise FacturaError("La factura requiere al menos un criterio identificado")


def crear_factura_emitida(
    *,
    entidad_id: str,
    tercero: Tercero,
    ejercicio: EjercicioContable,
    hecho_ids: tuple[str, ...],
    interpretacion_id: str,
    decision_id: str,
    criterio_ids: tuple[str, ...],
    representacion_id: str,
    autorizacion_id: str,
    fecha: datetime,
    base_centimos: int,
    iva_pct: float,
    numero_factura: str,
) -> ResultadoFactura:
    _validar_factura(entidad_id=entidad_id, tercero=tercero, ejercicio=ejercicio,
                     fecha=fecha, numero_factura=numero_factura,
                     representacion_id=representacion_id, hecho_ids=hecho_ids,
                     interpretacion_id=interpretacion_id, decision_id=decision_id,
                     criterio_ids=criterio_ids)

    if base_centimos <= 0:
        raise FacturaError("La base de una factura emitida debe ser positiva")

    iva = calcular_iva(base_centimos, iva_pct)
    total = base_centimos + iva

    movimiento = MovimientoEconomico(
        movimiento_id=f"MOV-{numero_factura}",
        entidad_id=entidad_id,
        tercero_id=tercero.tercero_id,
        tipo="FACTURA_EMITIDA",
        importe=total,
        fecha_documental=fecha,
        estado="EMITIDA_PENDIENTE_COBRO",
    )

    representacion = RepresentacionContable(
        representacion_id=representacion_id,
        hecho_ids=hecho_ids,
        interpretacion_id=interpretacion_id,
        decision_id=decision_id,
        criterio_ids=criterio_ids,
        marco="PGC_PYMES",
        fecha_contable=fecha,
        lineas=(
            Linea("430", debe=total),
            Linea("705", haber=base_centimos),
            Linea("477", haber=iva),
        ),
        autorizacion_id=autorizacion_id,
    )

    if not representacion.cuadra():
        raise FacturaError("La representación contable no cuadra")

    return ResultadoFactura(
        tercero=tercero,
        movimiento=movimiento,
        representacion=representacion,
    )


def crear_factura_recibida(
    *,
    entidad_id: str,
    tercero: Tercero,
    ejercicio: EjercicioContable,
    hecho_ids: tuple[str, ...],
    interpretacion_id: str,
    decision_id: str,
    criterio_ids: tuple[str, ...],
    representacion_id: str,
    autorizacion_id: str,
    fecha: datetime,
    base_centimos: int,
    iva_pct: float,
    cuenta_gasto: str,
    numero_factura: str,
) -> ResultadoFactura:
    if not cuenta_gasto or not cuenta_gasto.startswith("6"):
        raise FacturaError("Se requiere una cuenta de gasto del grupo 6")
    _validar_factura(entidad_id=entidad_id, tercero=tercero, ejercicio=ejercicio,
                     fecha=fecha, numero_factura=numero_factura,
                     representacion_id=representacion_id, hecho_ids=hecho_ids,
                     interpretacion_id=interpretacion_id, decision_id=decision_id,
                     criterio_ids=criterio_ids)

    if base_centimos <= 0:
        raise FacturaError("La base de una factura recibida debe ser positiva")

    iva = calcular_iva(base_centimos, iva_pct)
    total = base_centimos + iva

    movimiento = MovimientoEconomico(
        movimiento_id=f"MOV-{numero_factura}",
        entidad_id=entidad_id,
        tercero_id=tercero.tercero_id,
        tipo="FACTURA_RECIBIDA",
        importe=total,
        fecha_documental=fecha,
        estado="RECIBIDA_PENDIENTE_PAGO",
    )

    representacion = RepresentacionContable(
        representacion_id=representacion_id,
        hecho_ids=hecho_ids,
        interpretacion_id=interpretacion_id,
        decision_id=decision_id,
        criterio_ids=criterio_ids,
        marco="PGC_PYMES",
        fecha_contable=fecha,
        lineas=(
            Linea(cuenta_gasto, debe=base_centimos),
            Linea("472", debe=iva),
            Linea("400", haber=total),
        ),
        autorizacion_id=autorizacion_id,
    )

    if not representacion.cuadra():
        raise FacturaError("La representación contable no cuadra")

    return ResultadoFactura(
        tercero=tercero,
        movimiento=movimiento,
        representacion=representacion,
    )
