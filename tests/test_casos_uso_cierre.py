"""Pruebas del cierre integral, autorización y reconstrucción en memoria."""
from datetime import datetime

import pytest

from conta_rizoma4.dominio import (
    Actor,
    Autorizacion,
    CierreContable,
    EjercicioContable,
    EstadoRepresentacion,
    Linea,
    NucleoEpistemicoContable,
    RepresentacionContable,
    Rol,
)
from conta_rizoma4.dominio.casos_uso.cierre import (
    CierreError,
    cerrar_ejercicio,
    preparar_cierre_integral,
    reabrir_ejercicio,
)


INICIO = datetime(2025, 1, 1)
FIN = datetime(2025, 12, 31)
CIERRE_REGISTRADO = datetime(2025, 12, 31, 12)


def _representacion():
    return RepresentacionContable(
        representacion_id="R-1",
        hecho_ids=("H-1",),
        interpretacion_id="I-1",
        decision_id="D-1",
        criterio_ids=("C-1",),
        marco="PGC_PYMES",
        fecha_contable=FIN,
        lineas=(
            Linea("572", debe=150_000),
            Linea("600", debe=20_000),
            Linea("100", haber=100_000),
            Linea("705", haber=70_000),
        ),
        autorizacion_id="A-1",
        estado=EstadoRepresentacion.REGISTRADA,
    )


def _nucleo_con_ejercicio(*, actor_id="CONTADOR", rol=Rol.SUBDIRECTOR):
    nucleo = NucleoEpistemicoContable()
    nucleo.registrar_actor(Actor(actor_id, actor_id, rol=rol), INICIO)
    nucleo.registrar_actor(Actor("AUTORIZADOR", "Autorizador"), INICIO)
    ejercicio = EjercicioContable("E-2025", "EMP-A", INICIO, FIN)
    nucleo.registrar_ejercicio(ejercicio, actor_id, INICIO)
    nucleo.representaciones["R-1"] = _representacion()
    nucleo.otorgar_autorizacion(Autorizacion(
        "AUT-CIERRE", "AUTORIZADOR", "CIERRE_EJERCICIO", "E-2025", FIN,
    ))
    return nucleo, ejercicio


def test_prepara_regularizacion_cierre_y_apertura_sin_alterar_fuentes():
    ejercicio = EjercicioContable("E-2025", "EMP-A", INICIO, FIN)
    representacion = _representacion()
    cierre = preparar_cierre_integral(
        ejercicio, [representacion], cierre_id="C-1",
        fecha_cierre=FIN, registrado_en=CIERRE_REGISTRADO,
    )

    assert cierre.resultado_ejercicio == 50_000
    assert [(l.cuenta, l.debe, l.haber) for l in cierre.regularizacion] == [
        ("600", 0, 20_000), ("705", 70_000, 0), ("129", 0, 50_000),
    ]
    assert sum(l.debe for l in cierre.asiento_cierre) == sum(l.haber for l in cierre.asiento_cierre)
    assert all(
        (apertura.cuenta, apertura.debe, apertura.haber)
        == (cierre_linea.cuenta, cierre_linea.haber, cierre_linea.debe)
        for apertura, cierre_linea in zip(cierre.asiento_apertura, cierre.asiento_cierre)
    )
    assert representacion.estado == EstadoRepresentacion.REGISTRADA


def test_no_prepara_cierre_sin_representaciones_fuente():
    ejercicio = EjercicioContable("E-2025", "EMP-A", INICIO, FIN)
    with pytest.raises(CierreError, match="al menos una representación"):
        preparar_cierre_integral(
            ejercicio, [], cierre_id="C-VACIO",
            fecha_cierre=FIN, registrado_en=CIERRE_REGISTRADO,
        )


def test_responsable_no_puede_autorizar_su_propio_cierre():
    from conta_rizoma4.dominio import ErrorDominio

    nucleo, _ = _nucleo_con_ejercicio()
    nucleo.otorgar_autorizacion(Autorizacion(
        "AUT-PROPIA", "CONTADOR", "CIERRE_EJERCICIO", "E-2025", FIN,
    ))
    cierre = CierreContable(
        cierre_id="CIERRE-SELF", ejercicio_id="E-2025", fecha_cierre=FIN,
        registrado_en=CIERRE_REGISTRADO, regularizacion=(), asiento_cierre=(),
        asiento_apertura=(), representacion_ids=(), resultado_ejercicio=0,
    )

    with pytest.raises(ErrorDominio, match="no puede autorizar su propio cierre"):
        nucleo.registrar_cierre_ejercicio(
            cierre, "CONTADOR", "AUT-PROPIA", "Cierre",
        )


def test_cierre_exige_subdirector():
    nucleo, ejercicio = _nucleo_con_ejercicio(
        actor_id="JEFE", rol=Rol.JEFE_CONTABILIDAD,
    )
    with pytest.raises(CierreError, match="no tiene competencia"):
        cerrar_ejercicio(
            ejercicio, "JEFE", "AUT-CIERRE", FIN,
            nucleo=nucleo, representaciones=[_representacion()], cierre_id="CIERRE-JEFE",
            registrado_en=CIERRE_REGISTRADO, motivo="Cierre sin rango de subdirector",
        )


def test_cierra_con_autorizacion_y_reconstruye_cierre_y_reapertura():
    nucleo, ejercicio = _nucleo_con_ejercicio()
    cerrado = cerrar_ejercicio(
        ejercicio, "CONTADOR", "AUT-CIERRE", FIN,
        nucleo=nucleo, representaciones=[_representacion()], cierre_id="CIERRE-1",
        registrado_en=CIERRE_REGISTRADO, motivo="Cierre anual revisado",
    )
    assert cerrado.estado == "CERRADO"
    assert len(nucleo.cierres) == 1
    assert nucleo.cierres[0].representacion_ids == ("R-1",)
    from conta_rizoma4.dominio import Tercero
    from conta_rizoma4.dominio.casos_uso.tesoreria import TesoreriaError, registrar_cobro
    with pytest.raises(TesoreriaError, match="no está abierto"):
        registrar_cobro(
            entidad_id="EMP-A", tercero=Tercero("T-0", "JURIDICA", "Cliente"),
            ejercicio=ejercicio, hecho_ids=("H-0",), interpretacion_id="I-0",
            decision_id="D-0", criterio_ids=("C-1",), representacion_id="R-0",
            autorizacion_id="A-0",
            fecha=datetime(2025, 12, 30), importe_centimos=1_000, movimiento_id="M-0",
        )

    nucleo.otorgar_autorizacion(Autorizacion(
        "AUT-REABRIR", "AUTORIZADOR", "REAPERTURA_EJERCICIO", "E-2025",
        datetime(2026, 1, 14),
    ))
    reabierto = reabrir_ejercicio(
        ejercicio, "CONTADOR", "AUT-REABRIR", "Error detectado en factura",
        datetime(2026, 1, 15), nucleo=nucleo,
    )
    assert reabierto.estado == "REABIERTO"
    assert len(nucleo.cierres) == 1  # el cierre previo permanece
    movimiento, representacion = registrar_cobro(
        entidad_id="EMP-A", tercero=Tercero("T-1", "JURIDICA", "Cliente"),
        ejercicio=ejercicio, hecho_ids=("H-2",), interpretacion_id="I-2",
        decision_id="D-2", criterio_ids=("C-1",), representacion_id="R-2",
        autorizacion_id="A-2",
        fecha=datetime(2025, 12, 30), importe_centimos=1_000, movimiento_id="M-2",
    )
    assert movimiento.importe == 1_000 and representacion.cuadra()

    antes = nucleo.reconstruir(datetime(2026, 1, 14))
    despues = nucleo.reconstruir(datetime(2026, 1, 15))
    assert antes["ejercicios"]["E-2025"]["estado"] == "CERRADO"
    assert despues["ejercicios"]["E-2025"]["estado"] == "REABIERTO"
    assert len(despues["cierres"]) == 1
    assert despues["cierres"][0]["asiento_cierre"]

    # La reconstrucción procede del ledger; no depende del agregado mutable.
    nucleo.cierres.clear()
    assert len(nucleo.reconstruir(datetime(2026, 1, 15))["cierres"]) == 1


def test_reapertura_exige_subdirector():
    nucleo = NucleoEpistemicoContable()
    nucleo.registrar_actor(
        Actor("SUB", "Subdirector", rol=Rol.SUBDIRECTOR), INICIO,
    )
    nucleo.registrar_actor(
        Actor("JEFE", "Jefe", rol=Rol.JEFE_CONTABILIDAD), INICIO,
    )
    nucleo.registrar_actor(Actor("AUTORIZADOR", "Autorizador"), INICIO)
    ejercicio = EjercicioContable("E-2025", "EMP-A", INICIO, FIN)
    nucleo.registrar_ejercicio(ejercicio, "SUB", INICIO)
    nucleo.representaciones["R-1"] = _representacion()
    nucleo.otorgar_autorizacion(Autorizacion(
        "AUT-CIERRE", "AUTORIZADOR", "CIERRE_EJERCICIO", "E-2025", FIN,
    ))
    cerrar_ejercicio(
        ejercicio, "SUB", "AUT-CIERRE", FIN,
        nucleo=nucleo, representaciones=[_representacion()], cierre_id="CIERRE-1",
        registrado_en=CIERRE_REGISTRADO, motivo="Cierre anual revisado",
    )
    nucleo.otorgar_autorizacion(Autorizacion(
        "AUT-REABRIR", "AUTORIZADOR", "REAPERTURA_EJERCICIO", "E-2025",
        datetime(2026, 1, 14),
    ))

    with pytest.raises(CierreError, match="no tiene competencia"):
        reabrir_ejercicio(
            ejercicio, "JEFE", "AUT-REABRIR", "Error detectado",
            datetime(2026, 1, 15), nucleo=nucleo,
        )


def test_reapertura_sin_motivo_o_autorizacion_no_cambia_estado():
    nucleo, ejercicio = _nucleo_con_ejercicio()
    cerrar_ejercicio(
        ejercicio, "CONTADOR", "AUT-CIERRE", FIN,
        nucleo=nucleo, representaciones=[_representacion()], cierre_id="CIERRE-1",
        registrado_en=CIERRE_REGISTRADO, motivo="Cierre anual revisado",
    )
    nucleo.otorgar_autorizacion(Autorizacion(
        "AUT-REABRIR", "AUTORIZADOR", "REAPERTURA_EJERCICIO", "E-2025",
        datetime(2026, 1, 14),
    ))
    with pytest.raises(CierreError, match="motivo"):
        reabrir_ejercicio(
            ejercicio, "CONTADOR", "AUT-REABRIR", "", datetime(2026, 1, 15),
            nucleo=nucleo,
        )
    assert ejercicio.estado == "CERRADO"


def test_autorizacion_con_competencia_incorrecta_no_cierra():
    nucleo, ejercicio = _nucleo_con_ejercicio()
    nucleo.otorgar_autorizacion(Autorizacion(
        "AUT-EQUIVOCADA", "AUTORIZADOR", "REAPERTURA_EJERCICIO", "E-2025", FIN,
    ))
    with pytest.raises(CierreError, match="no cubre"):
        cerrar_ejercicio(
            ejercicio, "CONTADOR", "AUT-EQUIVOCADA", FIN,
            nucleo=nucleo, representaciones=[_representacion()], cierre_id="CIERRE-1",
            registrado_en=CIERRE_REGISTRADO, motivo="Cierre anual revisado",
        )
    assert ejercicio.estado == "ABIERTO"
    assert not nucleo.cierres


def test_ejercicio_reabierto_puede_volver_a_cerrarse_sin_perder_el_cierre_anterior():
    nucleo, ejercicio = _nucleo_con_ejercicio()
    cerrar_ejercicio(
        ejercicio, "CONTADOR", "AUT-CIERRE", FIN,
        nucleo=nucleo, representaciones=[_representacion()], cierre_id="CIERRE-1",
        registrado_en=CIERRE_REGISTRADO, motivo="Cierre inicial",
    )
    nucleo.otorgar_autorizacion(Autorizacion(
        "AUT-REABRIR", "AUTORIZADOR", "REAPERTURA_EJERCICIO", "E-2025",
        datetime(2026, 1, 14),
    ))
    reabrir_ejercicio(
        ejercicio, "CONTADOR", "AUT-REABRIR", "Rectificación aprobada",
        datetime(2026, 1, 15), nucleo=nucleo,
    )
    nucleo.otorgar_autorizacion(Autorizacion(
        "AUT-CIERRE-2", "AUTORIZADOR", "CIERRE_EJERCICIO", "E-2025",
        datetime(2026, 1, 16),
    ))
    cerrar_ejercicio(
        ejercicio, "CONTADOR", "AUT-CIERRE-2", FIN,
        nucleo=nucleo, representaciones=[_representacion()], cierre_id="CIERRE-2",
        registrado_en=datetime(2026, 1, 17), motivo="Nuevo cierre tras rectificación",
    )
    assert ejercicio.estado == "CERRADO"
    assert [c.cierre_id for c in nucleo.cierres] == ["CIERRE-1", "CIERRE-2"]


def test_cierre_rechaza_mayor_descuadrado_y_cuenta_no_clasificada():
    ejercicio = EjercicioContable("E-2025", "EMP-A", INICIO, FIN)
    representacion = _representacion()
    representacion.lineas = (Linea("572", debe=10), Linea("100", haber=9))
    with pytest.raises(CierreError, match="descuadrada"):
        preparar_cierre_integral(
            ejercicio, [representacion], cierre_id="C-1",
            fecha_cierre=FIN, registrado_en=CIERRE_REGISTRADO,
        )

    representacion = _representacion()
    representacion.lineas = (Linea("872", debe=10), Linea("572", haber=10))
    with pytest.raises(CierreError, match="no implementada"):
        preparar_cierre_integral(
            ejercicio, [representacion], cierre_id="C-1",
            fecha_cierre=FIN, registrado_en=CIERRE_REGISTRADO,
        )
