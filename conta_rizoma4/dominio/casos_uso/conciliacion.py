"""Conciliación bancaria en memoria; no importa extractos ni genera asientos."""
from __future__ import annotations

from dataclasses import dataclass

from ..entidades.economicas import Conciliacion, CuentaBancaria, MovimientoEconomico, MovimientoExtracto


class ConciliacionError(ValueError):
    """Incompatibilidad entre el movimiento bancario y el movimiento económico."""


@dataclass(frozen=True)
class ResumenConciliacion:
    saldo_inicial_banco: int
    saldo_inicial_libros: int
    saldo_final_banco: int
    saldo_final_libros: int
    diferencia_saldos: int
    extractos_sin_conciliar: tuple[str, ...]
    movimientos_sin_conciliar: tuple[str, ...]


def importe_bancario_firmado(movimiento: MovimientoEconomico) -> int:
    """Convención explícita: cobros/anticipos entran; pagos salen."""
    if movimiento.tipo in {"COBRO", "ANTICIPO_CLIENTE"}:
        return movimiento.importe
    if movimiento.tipo == "PAGO":
        return -movimiento.importe
    raise ConciliacionError(f"Tipo sin convención bancaria definida: {movimiento.tipo}")


def conciliar_movimiento(
    *, conciliacion_id: str, cuenta: CuentaBancaria,
    extracto: MovimientoExtracto, movimiento: MovimientoEconomico,
) -> Conciliacion:
    """Propone un vínculo 1:1; no cambia los movimientos originales."""
    if not conciliacion_id:
        raise ConciliacionError("conciliacion_id es obligatorio")
    if extracto.cuenta_id != cuenta.cuenta_id:
        raise ConciliacionError("El movimiento de extracto pertenece a otra cuenta")
    if movimiento.entidad_id != cuenta.entidad_id:
        raise ConciliacionError("El movimiento económico pertenece a otra entidad")
    if not cuenta.activa:
        raise ConciliacionError("La cuenta bancaria está inactiva")
    if extracto.estado != "NO_CONCILIADO":
        raise ConciliacionError("El movimiento de extracto ya está conciliado")
    estados_cobrados = {"COBRADO", "PAGADO", "ANTICIPO_PENDIENTE_FACTURA"}
    if movimiento.estado not in estados_cobrados:
        raise ConciliacionError("El movimiento económico todavía no está cobrado o pagado")
    esperado = importe_bancario_firmado(movimiento)
    if movimiento.moneda != cuenta.moneda:
        raise ConciliacionError("La moneda del movimiento no coincide con la cuenta")
    diferencia = extracto.importe - esperado
    return Conciliacion(
        conciliacion_id=conciliacion_id,
        movimiento_extracto_id=extracto.movimiento_id,
        movimiento_economico_id=movimiento.movimiento_id,
        estado="CONCILIADO" if diferencia == 0 else "DIFERENCIA",
        diferencia=diferencia,
        motivo="" if diferencia == 0 else "El importe del extracto no coincide con el movimiento económico",
    )


def resumir_conciliacion(
    *, cuenta: CuentaBancaria, saldo_inicial_banco: int, saldo_inicial_libros: int,
    extractos: tuple[MovimientoExtracto, ...], movimientos: tuple[MovimientoEconomico, ...],
    conciliaciones: tuple[Conciliacion, ...],
) -> ResumenConciliacion:
    """Calcula saldos y pendientes sobre snapshots proporcionados por quien llama."""
    ids_extracto = [e.movimiento_id for e in extractos]
    ids_movimiento = [m.movimiento_id for m in movimientos]
    if len(ids_extracto) != len(set(ids_extracto)):
        raise ConciliacionError("Hay identificadores de extracto duplicados")
    if len(ids_movimiento) != len(set(ids_movimiento)):
        raise ConciliacionError("Hay identificadores de movimiento económico duplicados")
    extracto_por_id = {e.movimiento_id: e for e in extractos}
    movimiento_por_id = {m.movimiento_id: m for m in movimientos}
    ids_conciliacion = [c.conciliacion_id for c in conciliaciones]
    if len(ids_conciliacion) != len(set(ids_conciliacion)):
        raise ConciliacionError("Hay identificadores de conciliación duplicados")
    extractos_conciliados: set[str] = set()
    movimientos_conciliados: set[str] = set()
    for c in conciliaciones:
        extracto = extracto_por_id.get(c.movimiento_extracto_id)
        movimiento = movimiento_por_id.get(c.movimiento_economico_id)
        if extracto is None or movimiento is None:
            raise ConciliacionError("La conciliación referencia movimientos ausentes del snapshot")
        if extracto.cuenta_id != cuenta.cuenta_id:
            raise ConciliacionError("La conciliación referencia un extracto de otra cuenta")
        if movimiento.entidad_id != cuenta.entidad_id or movimiento.moneda != cuenta.moneda:
            raise ConciliacionError("La conciliación referencia un movimiento de otra entidad o moneda")
        diferencia_real = extracto.importe - importe_bancario_firmado(movimiento)
        if c.estado == "CONCILIADO":
            if c.diferencia != 0 or diferencia_real != 0:
                raise ConciliacionError("Un vínculo conciliado debe tener diferencia cero")
            if c.movimiento_extracto_id in extractos_conciliados or c.movimiento_economico_id in movimientos_conciliados:
                raise ConciliacionError("Un movimiento no puede figurar en más de un vínculo conciliado")
            extractos_conciliados.add(c.movimiento_extracto_id)
            movimientos_conciliados.add(c.movimiento_economico_id)
        elif c.estado == "DIFERENCIA":
            if c.diferencia != diferencia_real:
                raise ConciliacionError("La diferencia registrada no coincide con los movimientos")
        else:
            raise ConciliacionError(f"Estado de conciliación no admitido: {c.estado}")

    extractos_cuenta = tuple(e for e in extractos if e.cuenta_id == cuenta.cuenta_id)
    enlazados = {c.movimiento_extracto_id for c in conciliaciones if c.estado == "CONCILIADO"}
    mov_enlazados = {c.movimiento_economico_id for c in conciliaciones if c.estado == "CONCILIADO"}
    tipos_tesoreria = {"COBRO", "PAGO", "ANTICIPO_CLIENTE"}
    mov_entidad = tuple(
        m for m in movimientos
        if m.entidad_id == cuenta.entidad_id and m.moneda == cuenta.moneda and m.tipo in tipos_tesoreria
    )
    saldo_banco = saldo_inicial_banco + sum(e.importe for e in extractos_cuenta)
    saldo_libros = saldo_inicial_libros + sum(importe_bancario_firmado(m) for m in mov_entidad)
    return ResumenConciliacion(
        saldo_inicial_banco=saldo_inicial_banco, saldo_inicial_libros=saldo_inicial_libros,
        saldo_final_banco=saldo_banco, saldo_final_libros=saldo_libros,
        diferencia_saldos=saldo_banco - saldo_libros,
        extractos_sin_conciliar=tuple(e.movimiento_id for e in extractos_cuenta if e.movimiento_id not in enlazados),
        movimientos_sin_conciliar=tuple(m.movimiento_id for m in mov_entidad if m.movimiento_id not in mov_enlazados),
    )
