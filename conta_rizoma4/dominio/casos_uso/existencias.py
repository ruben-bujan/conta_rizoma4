"""Casos de uso básicos de existencias."""
from __future__ import annotations

from datetime import datetime
from dataclasses import dataclass

from ..entidades.economicas import EjercicioContable
from ..entidades.contables import Linea, RepresentacionContable


class ExistenciasError(ValueError):
    pass


@dataclass(frozen=True)
class LoteExistencias:
    cantidad: int
    coste_total_centimos: int

    def __post_init__(self) -> None:
        if not isinstance(self.cantidad, int) or isinstance(self.cantidad, bool) or self.cantidad <= 0:
            raise ValueError("La cantidad del lote debe ser un entero positivo")
        if not isinstance(self.coste_total_centimos, int) or self.coste_total_centimos < 0:
            raise ValueError("El coste del lote debe ser un entero no negativo")


@dataclass(frozen=True)
class SalidaValorada:
    coste_salida_centimos: int
    lotes_restantes: tuple[LoteExistencias, ...]


def valorar_salida_existencias(
    *, lotes: tuple[LoteExistencias, ...], cantidad: int, metodo: str,
) -> SalidaValorada:
    """Valora salida FIFO o PMP a partir de lotes en el orden de entrada."""
    if not isinstance(cantidad, int) or isinstance(cantidad, bool) or cantidad <= 0:
        raise ExistenciasError("La cantidad de salida debe ser un entero positivo")
    cantidad_disponible = sum(lote.cantidad for lote in lotes)
    if cantidad > cantidad_disponible:
        raise ExistenciasError("La salida excede las existencias disponibles")
    if metodo not in {"FIFO", "PMP"}:
        raise ExistenciasError("Método de valoración no admitido")

    coste_total = sum(lote.coste_total_centimos for lote in lotes)
    if metodo == "PMP":
        coste_salida = (coste_total * cantidad * 2 + cantidad_disponible) // (2 * cantidad_disponible)
        cantidad_restante = cantidad_disponible - cantidad
        coste_restante = coste_total - coste_salida
        restantes = (
            (LoteExistencias(cantidad_restante, coste_restante),) if cantidad_restante else ()
        )
        return SalidaValorada(coste_salida, restantes)

    pendiente = cantidad
    coste_salida = 0
    restantes: list[LoteExistencias] = []
    for indice, lote in enumerate(lotes):
        base, resto = divmod(lote.coste_total_centimos, lote.cantidad)
        consumidas = min(pendiente, lote.cantidad)
        coste_salida += base * consumidas + min(resto, consumidas)
        pendiente -= consumidas
        if consumidas < lote.cantidad:
            restantes.append(LoteExistencias(
                lote.cantidad - consumidas,
                lote.coste_total_centimos - (base * consumidas + min(resto, consumidas)),
            ))
        if pendiente == 0:
            # Conserva en orden las capas aún no consumidas.
            restantes.extend(lotes[indice + 1:])
            break
    return SalidaValorada(coste_salida, tuple(restantes))


def compra_existencias(
    *, entidad_id: str, ejercicio: EjercicioContable,
    representacion_id: str, interpretacion_id: str, decision_id: str,
    criterio_ids: tuple[str, ...], hecho_ids: tuple[str, ...],
    autorizacion_id: str, fecha: datetime, base_centimos: int,
    cuenta_existencias: str,
) -> RepresentacionContable:
    if entidad_id != ejercicio.entidad_id:
        raise ExistenciasError("Entidad distinta del ejercicio")
    if base_centimos <= 0:
        raise ExistenciasError("El importe debe ser positivo")
    if not cuenta_existencias:
        raise ExistenciasError("Cuenta de existencias obligatoria")
    if not ejercicio.permite_registro:
        raise ExistenciasError("Ejercicio no abierto")
    if not ejercicio.inicio <= fecha <= ejercicio.fin:
        raise ExistenciasError("Fecha fuera del ejercicio")

    representacion = RepresentacionContable(
        representacion_id, hecho_ids, interpretacion_id, decision_id,
        criterio_ids, "PGC_PYMES", fecha,
        (Linea(cuenta_existencias, debe=base_centimos), Linea("400", haber=base_centimos)),
        autorizacion_id=autorizacion_id,
    )
    if not representacion.cuadra():
        raise ExistenciasError("Representación descuadrada")
    return representacion


def venta_existencias(
    *, entidad_id: str, ejercicio: EjercicioContable,
    representacion_id: str, interpretacion_id: str, decision_id: str,
    criterio_ids: tuple[str, ...], hecho_ids: tuple[str, ...],
    autorizacion_id: str, fecha: datetime, importe_centimos: int,
    cuenta_ingreso: str,
) -> RepresentacionContable:
    if entidad_id != ejercicio.entidad_id:
        raise ExistenciasError("Entidad distinta del ejercicio")
    if importe_centimos <= 0:
        raise ExistenciasError("El importe debe ser positivo")
    if not cuenta_ingreso:
        raise ExistenciasError("Cuenta de ingreso obligatoria")
    if not ejercicio.permite_registro:
        raise ExistenciasError("Ejercicio no abierto")
    if not ejercicio.inicio <= fecha <= ejercicio.fin:
        raise ExistenciasError("Fecha fuera del ejercicio")

    representacion = RepresentacionContable(
        representacion_id, hecho_ids, interpretacion_id, decision_id,
        criterio_ids, "PGC_PYMES", fecha,
        (Linea("430", debe=importe_centimos), Linea(cuenta_ingreso, haber=importe_centimos)),
        autorizacion_id=autorizacion_id,
    )
    if not representacion.cuadra():
        raise ExistenciasError("Representación descuadrada")
    return representacion
