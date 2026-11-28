"""Regularización, cierre y reapertura autorizada en memoria."""
from __future__ import annotations

from datetime import datetime
from typing import Iterable

from ..entidades.contables import CierreContable, EstadoRepresentacion, Linea, RepresentacionContable
from ..entidades.economicas import EjercicioContable
from ..excepciones import ErrorDominio
from ..servicios.nucleo import NucleoEpistemicoContable


class CierreError(ValueError):
    pass


def preparar_cierre_integral(
    ejercicio: EjercicioContable,
    representaciones: Iterable[RepresentacionContable],
    *,
    cierre_id: str,
    fecha_cierre: datetime,
    registrado_en: datetime,
) -> CierreContable:
    """Calcula hoja de cierre y apertura desde representaciones registradas.

    Las líneas producidas son propuestas derivadas: no se agregan al mayor.
    Signo de saldo: debe menos haber.
    """
    if not cierre_id:
        raise CierreError("cierre_id es obligatorio")
    if fecha_cierre < ejercicio.fin:
        raise CierreError("La fecha de cierre no puede preceder al fin del ejercicio")
    if registrado_en < fecha_cierre:
        raise CierreError("El cierre no puede registrarse antes de su fecha contable")

    reps = tuple(representaciones)
    if not reps:
        raise CierreError("El cierre requiere al menos una representación contable fuente")
    if len({r.representacion_id for r in reps}) != len(reps):
        raise CierreError("Hay representaciones duplicadas en el cierre")
    saldos: dict[str, int] = {}
    for rep in reps:
        if rep.estado != EstadoRepresentacion.REGISTRADA:
            raise CierreError(f"La representación {rep.representacion_id} no está registrada")
        if not ejercicio.inicio <= rep.fecha_contable <= ejercicio.fin:
            raise CierreError(f"La representación {rep.representacion_id} queda fuera del ejercicio")
        if not rep.lineas or not rep.cuadra():
            raise CierreError(f"La representación {rep.representacion_id} está vacía o descuadrada")
        for linea in rep.lineas:
            if not linea.cuenta or not linea.cuenta[0].isdigit():
                raise CierreError(f"Cuenta no clasificable: {linea.cuenta!r}")
            grupo = linea.cuenta[0]
            if grupo not in "1234567":
                raise CierreError(f"La cuenta {linea.cuenta} requiere una regla de cierre no implementada")
            saldos[linea.cuenta] = saldos.get(linea.cuenta, 0) + linea.debe - linea.haber

    if sum(saldos.values()) != 0:
        raise CierreError("El balance de comprobación agregado no cuadra")

    regularizacion: list[Linea] = []
    for cuenta, saldo in sorted(saldos.items()):
        if cuenta[0] not in "67" or saldo == 0:
            continue
        if saldo > 0:
            regularizacion.append(Linea(cuenta, haber=saldo))
        else:
            regularizacion.append(Linea(cuenta, debe=-saldo))

    debe = sum(l.debe for l in regularizacion)
    haber = sum(l.haber for l in regularizacion)
    if debe > haber:
        regularizacion.append(Linea("129", haber=debe - haber))
    elif haber > debe:
        regularizacion.append(Linea("129", debe=haber - debe))
    resultado = sum(l.haber - l.debe for l in regularizacion if l.cuenta == "129")

    saldos_tras_regularizacion = dict(saldos)
    for linea in regularizacion:
        saldos_tras_regularizacion[linea.cuenta] = (
            saldos_tras_regularizacion.get(linea.cuenta, 0) + linea.debe - linea.haber
        )
    if any(saldo for cuenta, saldo in saldos_tras_regularizacion.items() if cuenta[0] in "67"):
        raise CierreError("La regularización no ha dejado a cero las cuentas 6 y 7")

    asiento_cierre: list[Linea] = []
    for cuenta, saldo in sorted(saldos_tras_regularizacion.items()):
        if cuenta[0] not in "12345" and cuenta != "129":
            continue
        if saldo > 0:
            asiento_cierre.append(Linea(cuenta, haber=saldo))
        elif saldo < 0:
            asiento_cierre.append(Linea(cuenta, debe=-saldo))
    if sum(l.debe for l in asiento_cierre) != sum(l.haber for l in asiento_cierre):
        raise CierreError("El asiento de cierre propuesto no cuadra")
    asiento_apertura = tuple(
        Linea(l.cuenta, debe=l.haber, haber=l.debe) for l in asiento_cierre
    )
    return CierreContable(
        cierre_id=cierre_id,
        ejercicio_id=ejercicio.ejercicio_id,
        fecha_cierre=fecha_cierre,
        registrado_en=registrado_en,
        regularizacion=tuple(regularizacion),
        asiento_cierre=tuple(asiento_cierre),
        asiento_apertura=asiento_apertura,
        representacion_ids=tuple(sorted(r.representacion_id for r in reps)),
        resultado_ejercicio=resultado,
    )


def cerrar_ejercicio(
    ejercicio: EjercicioContable,
    actor_id: str,
    autorizacion_id: str,
    fecha_cierre: datetime,
    *,
    nucleo: NucleoEpistemicoContable,
    representaciones: Iterable[RepresentacionContable],
    cierre_id: str,
    registrado_en: datetime,
    motivo: str,
) -> EjercicioContable:
    """Calcula, registra y autoriza el cierre sin alterar las representaciones fuente."""
    if nucleo.ejercicios.get(ejercicio.ejercicio_id) is not ejercicio:
        raise CierreError("El ejercicio debe estar registrado en el núcleo en memoria")
    representaciones = tuple(representaciones)
    if any(nucleo.representaciones.get(r.representacion_id) != r for r in representaciones):
        raise CierreError("El cierre debe usar las representaciones registradas en el núcleo")
    cierre = preparar_cierre_integral(
        ejercicio, representaciones, cierre_id=cierre_id,
        fecha_cierre=fecha_cierre, registrado_en=registrado_en,
    )
    try:
        nucleo.registrar_cierre_ejercicio(cierre, actor_id, autorizacion_id, motivo)
    except ErrorDominio as exc:
        raise CierreError(str(exc)) from exc
    return ejercicio


def reabrir_ejercicio(
    ejercicio: EjercicioContable,
    actor_id: str,
    autorizacion_id: str,
    motivo: str,
    fecha_reapertura: datetime,
    *,
    nucleo: NucleoEpistemicoContable,
) -> EjercicioContable:
    """Registra reapertura autorizada sin borrar el cierre ni sus propuestas."""
    if nucleo.ejercicios.get(ejercicio.ejercicio_id) is not ejercicio:
        raise CierreError("El ejercicio debe estar registrado en el núcleo en memoria")
    try:
        return nucleo.registrar_reapertura_ejercicio(
            ejercicio.ejercicio_id, actor_id, autorizacion_id, motivo, fecha_reapertura,
        )
    except ErrorDominio as exc:
        raise CierreError(str(exc)) from exc
