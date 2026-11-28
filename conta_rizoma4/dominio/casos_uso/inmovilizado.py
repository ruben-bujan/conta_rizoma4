"""Casos de uso básicos de inmovilizado."""
from __future__ import annotations

from datetime import datetime

from ..entidades.economicas import EjercicioContable
from ..entidades.contables import Linea, RepresentacionContable


class InmovilizadoError(ValueError):
    pass


def calcular_cuota_amortizacion_lineal(
    *, coste_centimos: int, valor_residual_centimos: int,
    vida_util_periodos: int, periodos_ya_amortizados: int = 0,
) -> int:
    """Calcula una cuota uniforme con reparto del residuo de redondeo."""
    valores = (coste_centimos, valor_residual_centimos, vida_util_periodos, periodos_ya_amortizados)
    if any(not isinstance(v, int) or isinstance(v, bool) for v in valores):
        raise InmovilizadoError("Los parámetros de amortización deben ser enteros")
    if coste_centimos < 0 or valor_residual_centimos < 0 or valor_residual_centimos > coste_centimos:
        raise InmovilizadoError("Coste o valor residual no válido")
    if vida_util_periodos <= 0 or not 0 <= periodos_ya_amortizados:
        raise InmovilizadoError("Vida útil o periodos amortizados no válidos")
    if periodos_ya_amortizados >= vida_util_periodos:
        return 0
    base = coste_centimos - valor_residual_centimos
    cuota, resto = divmod(base, vida_util_periodos)
    return cuota + (1 if periodos_ya_amortizados < resto else 0)


def alta_inmovilizado(
    *, entidad_id: str, ejercicio: EjercicioContable,
    representacion_id: str, interpretacion_id: str, decision_id: str,
    criterio_ids: tuple[str, ...], hecho_ids: tuple[str, ...],
    autorizacion_id: str, fecha: datetime, coste_centimos: int,
    cuenta_activo: str,
) -> RepresentacionContable:
    if entidad_id != ejercicio.entidad_id:
        raise InmovilizadoError("Entidad distinta del ejercicio")
    if coste_centimos <= 0:
        raise InmovilizadoError("El coste debe ser positivo")
    if not cuenta_activo:
        raise InmovilizadoError("Cuenta de activo obligatoria")
    if not ejercicio.permite_registro:
        raise InmovilizadoError("Ejercicio no abierto")
    if not ejercicio.inicio <= fecha <= ejercicio.fin:
        raise InmovilizadoError("Fecha fuera del ejercicio")

    representacion = RepresentacionContable(
        representacion_id, hecho_ids, interpretacion_id, decision_id,
        criterio_ids, "PGC_PYMES", fecha,
        (Linea(cuenta_activo, debe=coste_centimos), Linea("400", haber=coste_centimos)),
        autorizacion_id=autorizacion_id,
    )
    if not representacion.cuadra():
        raise InmovilizadoError("Representación descuadrada")
    return representacion


def amortizar_inmovilizado(
    *, entidad_id: str, ejercicio: EjercicioContable,
    representacion_id: str, interpretacion_id: str, decision_id: str,
    criterio_ids: tuple[str, ...], hecho_ids: tuple[str, ...],
    autorizacion_id: str, fecha: datetime, importe_centimos: int,
    cuenta_gasto: str, cuenta_amortizacion: str,
) -> RepresentacionContable:
    if entidad_id != ejercicio.entidad_id:
        raise InmovilizadoError("Entidad distinta del ejercicio")
    if importe_centimos <= 0:
        raise InmovilizadoError("El importe debe ser positivo")
    if not cuenta_gasto or not cuenta_amortizacion:
        raise InmovilizadoError("Cuentas de gasto y amortización obligatorias")
    if not ejercicio.permite_registro:
        raise InmovilizadoError("Ejercicio no abierto")
    if not ejercicio.inicio <= fecha <= ejercicio.fin:
        raise InmovilizadoError("Fecha fuera del ejercicio")

    representacion = RepresentacionContable(
        representacion_id, hecho_ids, interpretacion_id, decision_id,
        criterio_ids, "PGC_PYMES", fecha,
        (Linea(cuenta_gasto, debe=importe_centimos), Linea(cuenta_amortizacion, haber=importe_centimos)),
        autorizacion_id=autorizacion_id,
    )
    if not representacion.cuadra():
        raise InmovilizadoError("Representación descuadrada")
    return representacion
