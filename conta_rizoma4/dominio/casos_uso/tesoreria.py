"""Casos de uso básicos de cobro, pago y anticipo."""
from __future__ import annotations

from datetime import datetime

from ..entidades.economicas import EjercicioContable, MovimientoEconomico, Tercero
from ..entidades.contables import Linea, RepresentacionContable


class TesoreriaError(ValueError):
    pass


def registrar_cobro(
    *, entidad_id: str,
    tercero: Tercero,
    ejercicio: EjercicioContable,
    hecho_ids: tuple[str, ...],
    interpretacion_id: str,
    decision_id: str,
    criterio_ids: tuple[str, ...],
    representacion_id: str,
    autorizacion_id: str,
    fecha: datetime,
    importe_centimos: int,
    movimiento_id: str,
):
    if importe_centimos < 0:
        raise TesoreriaError("El cobro no puede ser negativo")
    if not ejercicio.permite_registro:
        raise TesoreriaError("El ejercicio no está abierto")
    if not ejercicio.inicio <= fecha <= ejercicio.fin:
        raise TesoreriaError("El cobro está fuera del ejercicio")

    movimiento = MovimientoEconomico(
        movimiento_id=movimiento_id,
        entidad_id=entidad_id,
        tercero_id=tercero.tercero_id,
        tipo="COBRO",
        importe=importe_centimos,
        fecha_documental=fecha,
        estado="COBRADO",
    )
    representacion = RepresentacionContable(
        representacion_id=representacion_id,
        hecho_ids=hecho_ids,
        interpretacion_id=interpretacion_id,
        decision_id=decision_id,
        criterio_ids=criterio_ids,
        marco="PGC_ES",
        fecha_contable=fecha,
        lineas=(Linea("572", debe=importe_centimos), Linea("430", haber=importe_centimos)),
        autorizacion_id=autorizacion_id,
    )
    if not representacion.cuadra():
        raise TesoreriaError("El cobro no cuadra")
    return movimiento, representacion


def registrar_pago(
    *, entidad_id: str,
    tercero: Tercero,
    ejercicio: EjercicioContable,
    hecho_ids: tuple[str, ...],
    interpretacion_id: str,
    decision_id: str,
    criterio_ids: tuple[str, ...],
    representacion_id: str,
    autorizacion_id: str,
    fecha: datetime,
    importe_centimos: int,
    movimiento_id: str,
):
    if importe_centimos < 0:
        raise TesoreriaError("El pago no puede ser negativo")
    if not ejercicio.permite_registro:
        raise TesoreriaError("El ejercicio no está abierto")
    if not ejercicio.inicio <= fecha <= ejercicio.fin:
        raise TesoreriaError("El pago está fuera del ejercicio")

    movimiento = MovimientoEconomico(
        movimiento_id=movimiento_id,
        entidad_id=entidad_id,
        tercero_id=tercero.tercero_id,
        tipo="PAGO",
        importe=importe_centimos,
        fecha_documental=fecha,
        estado="PAGADO",
    )
    representacion = RepresentacionContable(
        representacion_id=representacion_id,
        hecho_ids=hecho_ids,
        interpretacion_id=interpretacion_id,
        decision_id=decision_id,
        criterio_ids=criterio_ids,
        marco="PGC_ES",
        fecha_contable=fecha,
        lineas=(Linea("400", debe=importe_centimos), Linea("572", haber=importe_centimos)),
        autorizacion_id=autorizacion_id,
    )
    if not representacion.cuadra():
        raise TesoreriaError("El pago no cuadra")
    return movimiento, representacion


def registrar_anticipo_cliente(
    *, entidad_id: str,
    tercero: Tercero,
    ejercicio: EjercicioContable,
    hecho_ids: tuple[str, ...],
    interpretacion_id: str,
    decision_id: str,
    criterio_ids: tuple[str, ...],
    representacion_id: str,
    autorizacion_id: str,
    fecha: datetime,
    importe_centimos: int,
    movimiento_id: str,
):
    if importe_centimos < 0:
        raise TesoreriaError("El anticipo no puede ser negativo")
    if not ejercicio.permite_registro:
        raise TesoreriaError("El ejercicio no está abierto")

    movimiento = MovimientoEconomico(
        movimiento_id=movimiento_id,
        entidad_id=entidad_id,
        tercero_id=tercero.tercero_id,
        tipo="ANTICIPO_CLIENTE",
        importe=importe_centimos,
        fecha_documental=fecha,
        estado="ANTICIPO_PENDIENTE_FACTURA",
    )
    representacion = RepresentacionContable(
        representacion_id=representacion_id,
        hecho_ids=hecho_ids,
        interpretacion_id=interpretacion_id,
        decision_id=decision_id,
        criterio_ids=criterio_ids,
        marco="PGC_ES",
        fecha_contable=fecha,
        lineas=(Linea("572", debe=importe_centimos), Linea("438", haber=importe_centimos)),
        autorizacion_id=autorizacion_id,
    )
    if not representacion.cuadra():
        raise TesoreriaError("El anticipo no cuadra")
    return movimiento, representacion
