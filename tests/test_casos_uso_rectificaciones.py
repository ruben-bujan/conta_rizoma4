"""Pruebas de rectificación y reclasificación formal."""
from datetime import datetime


def _representaciones():
    from conta_rizoma4.dominio import EstadoRepresentacion, Linea, RepresentacionContable

    original = RepresentacionContable(
        "R-ORIGINAL", ("H-1",), "I-1", "D-1", ("C-1",), "PGC_ES",
        datetime(2025, 4, 12),
        (Linea("430", debe=121000), Linea("705", haber=121000)),
        autorizacion_id="A-1",
        estado=EstadoRepresentacion.REGISTRADA,
    )
    nueva = RepresentacionContable(
        "R-NUEVA", ("H-1",), "I-2", "D-2", ("C-1",), "PGC_ES",
        datetime(2025, 4, 18),
        (Linea("572", debe=50000), Linea("430", haber=50000)),
        autorizacion_id="A-2",
    )
    return original, nueva


def test_reclasificacion_conserva_original():
    from conta_rizoma4.dominio.casos_uso.rectificaciones import reclasificar_representacion

    original, nueva = _representaciones()
    rectificacion = reclasificar_representacion(
        original=original,
        nueva=nueva,
        rectificacion_id="X-1",
        actor_id="CONTADOR",
        motivo="Cobro parcial acreditado",
        autorizacion_id="AUT-1",
        creada_en=datetime(2025, 4, 18),
    )

    assert rectificacion.representacion_original_id == "R-ORIGINAL"
    assert original.estado.value == "REGISTRADA"
    assert nueva.estado.value == "PROPUESTA"


def test_nucleo_registra_rectificacion_y_cambia_estado_en_evento():
    from conta_rizoma4.dominio import (
        Actor, Autorizacion, EstadoRepresentacion, NucleoEpistemicoContable, Rol,
    )
    from conta_rizoma4.dominio.casos_uso.rectificaciones import reclasificar_representacion

    original, nueva = _representaciones()
    nueva.estado = EstadoRepresentacion.REGISTRADA
    nucleo = NucleoEpistemicoContable()
    nucleo.registrar_actor(
        Actor("CONTADOR", "Contador", rol=Rol.JEFE_CONTABILIDAD), datetime(2025, 1, 1),
    )
    nucleo.registrar_actor(Actor("AUTORIZADOR", "Autorizador"), datetime(2025, 1, 1))
    nucleo.otorgar_autorizacion(Autorizacion(
        "AUT-1", "AUTORIZADOR", "RECTIFICAR", "R-ORIGINAL", datetime(2025, 4, 18),
    ))
    nucleo.representaciones[original.representacion_id] = original
    nucleo.representaciones[nueva.representacion_id] = nueva
    rectificacion = reclasificar_representacion(
        original=original, nueva=nueva, rectificacion_id="X-NUCLEO",
        actor_id="CONTADOR", motivo="Clasificación corregida",
        autorizacion_id="AUT-1", creada_en=datetime(2025, 4, 18),
    )

    nucleo.crear_rectificacion(rectificacion, "CONTADOR")
    assert original.estado == EstadoRepresentacion.RECTIFICADA
    assert nueva.estado == EstadoRepresentacion.REGISTRADA
    assert nucleo.eventos[-1].tipo == "RECTIFICACION_REGISTRADA"


def test_nucleo_rechaza_rectificacion_de_operario():
    import pytest
    from conta_rizoma4.dominio import (
        Actor, Autorizacion, ErrorDominio, EstadoRepresentacion,
        NucleoEpistemicoContable, Rol,
    )
    from conta_rizoma4.dominio.casos_uso.rectificaciones import reclasificar_representacion

    original, nueva = _representaciones()
    nueva.estado = EstadoRepresentacion.REGISTRADA
    nucleo = NucleoEpistemicoContable()
    nucleo.registrar_actor(
        Actor("CONTADOR", "Contador", rol=Rol.OPERARIO), datetime(2025, 1, 1),
    )
    nucleo.registrar_actor(Actor("AUTORIZADOR", "Autorizador"), datetime(2025, 1, 1))
    nucleo.otorgar_autorizacion(Autorizacion(
        "AUT-1", "AUTORIZADOR", "RECTIFICAR", "R-ORIGINAL", datetime(2025, 4, 18),
    ))
    nucleo.representaciones[original.representacion_id] = original
    nucleo.representaciones[nueva.representacion_id] = nueva
    rectificacion = reclasificar_representacion(
        original=original, nueva=nueva, rectificacion_id="X-OPERARIO",
        actor_id="CONTADOR", motivo="Clasificación corregida",
        autorizacion_id="AUT-1", creada_en=datetime(2025, 4, 18),
    )

    with pytest.raises(ErrorDominio, match="no tiene competencia"):
        nucleo.crear_rectificacion(rectificacion, "CONTADOR")


def test_sustitucion_rechaza_mismo_objeto():
    from conta_rizoma4.dominio.casos_uso.rectificaciones import RectificacionError, rectificar_representacion

    original, _ = _representaciones()

    try:
        rectificar_representacion(
            original=original,
            nueva=original,
            rectificacion_id="X-2",
            tipo="SUSTITUCION",
            causa="ERROR",
            motivo="Corrección",
            actor_id="CONTADOR",
            autorizacion_id="AUT-1",
            creada_en=datetime(2025, 4, 18),
        )
    except RectificacionError:
        return
    raise AssertionError("Debe rechazar sustitución por el mismo objeto")


def test_fecha_anterior_no_modifica_representacion_original():
    from conta_rizoma4.dominio import EstadoRepresentacion
    from conta_rizoma4.dominio.casos_uso.rectificaciones import RectificacionError, rectificar_representacion

    original, nueva = _representaciones()
    try:
        rectificar_representacion(
            original=original, nueva=nueva, rectificacion_id="X-3", tipo="SUSTITUCION",
            causa="ERROR", motivo="Corrección", actor_id="CONTADOR",
            autorizacion_id="AUT-1", creada_en=datetime(2025, 4, 1),
        )
    except RectificacionError:
        pass
    else:
        raise AssertionError("Debe rechazar una rectificación anterior")
    assert original.estado == EstadoRepresentacion.REGISTRADA
