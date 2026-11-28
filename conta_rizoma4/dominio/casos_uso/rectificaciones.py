"""Casos de uso de rectificación, reclasificación y sustitución."""
from __future__ import annotations

from datetime import datetime

from ..entidades.contables import EstadoRepresentacion, RepresentacionContable, Rectificacion


class RectificacionError(ValueError):
    pass


def rectificar_representacion(
    *,
    original: RepresentacionContable,
    nueva: RepresentacionContable,
    rectificacion_id: str,
    tipo: str,
    causa: str,
    motivo: str,
    actor_id: str,
    autorizacion_id: str | None,
    creada_en: datetime,
) -> Rectificacion:
    if not rectificacion_id or not actor_id:
        raise RectificacionError("La rectificación requiere identificador y actor")
    if original.representacion_id == nueva.representacion_id:
        raise RectificacionError("La rectificación requiere una representación nueva")
    if not tipo or not causa or not causa.strip():
        raise RectificacionError("La rectificación requiere tipo y causa")
    if original.estado != EstadoRepresentacion.REGISTRADA:
        raise RectificacionError("La representación original debe estar registrada y no rectificada")
    if nueva.estado not in {EstadoRepresentacion.PROPUESTA, EstadoRepresentacion.REGISTRADA}:
        raise RectificacionError("La representación nueva no puede estar rectificada")
    if creada_en < original.fecha_contable:
        raise RectificacionError("La rectificación no puede preceder a la representación original")
    if not nueva.cuadra():
        raise RectificacionError("La representación nueva no cuadra")
    if not motivo or not motivo.strip():
        raise RectificacionError("La rectificación requiere motivo")

    # Devuelve la operación propuesta. El núcleo cambia estados y registra el
    # evento al aceptar esta rectificación.
    return Rectificacion(
        rectificacion_id=rectificacion_id,
        representacion_original_id=original.representacion_id,
        representacion_nueva_id=nueva.representacion_id,
        tipo=tipo,
        causa=causa,
        motivo=motivo,
        actor_id=actor_id,
        autorizacion_id=autorizacion_id,
        creada_en=creada_en,
    )


def reclasificar_representacion(
    *, original: RepresentacionContable, nueva: RepresentacionContable,
    rectificacion_id: str, actor_id: str, motivo: str,
    autorizacion_id: str | None, creada_en: datetime,
) -> Rectificacion:
    return rectificar_representacion(
        original=original,
        nueva=nueva,
        rectificacion_id=rectificacion_id,
        tipo="RECLASIFICACION",
        causa="CAMBIO_CLASIFICACION",
        motivo=motivo,
        actor_id=actor_id,
        autorizacion_id=autorizacion_id,
        creada_en=creada_en,
    )


def sustituir_representacion(
    *, original: RepresentacionContable, nueva: RepresentacionContable,
    rectificacion_id: str, actor_id: str, motivo: str,
    causa: str, autorizacion_id: str | None, creada_en: datetime,
) -> Rectificacion:
    return rectificar_representacion(
        original=original,
        nueva=nueva,
        rectificacion_id=rectificacion_id,
        tipo="SUSTITUCION",
        causa=causa,
        motivo=motivo,
        actor_id=actor_id,
        autorizacion_id=autorizacion_id,
        creada_en=creada_en,
    )
