"""Pruebas de aceptación del vertical slice de la POC."""
from datetime import datetime

from .modelo import (
    Actor, Autorizacion, Criterio, Decision, EntidadContable,
    Evidencia, FechaEconomica, HechoEconomico, Interpretacion,
    Linea, Magnitud, Rectificacion, RepresentacionContable, Fuente,
    TipoFecha,
)
from .nucleo import ErrorDominio, NucleoEpistemicoContable


def fecha(dia: int) -> datetime:
    return datetime(2025, 4, dia)


def construir_vertical_slice():
    nucleo = NucleoEpistemicoContable()

    nucleo.registrar_actor(Actor("A-CONTABLE", "Contable principal"), fecha(1))
    nucleo.registrar_actor(Actor("A-AUTORIDAD", "Responsable económico"), fecha(1))

    nucleo.registrar_entidad(
        EntidadContable("EMP-A", "Empresa A"), "A-CONTABLE", fecha(1)
    )

    nucleo.registrar_fuente(
        Fuente("F-CONTRATO", "DOCUMENTAL", "Contrato firmado"),
        "A-CONTABLE", fecha(1),
    )
    nucleo.registrar_fuente(
        Fuente("F-BANCO", "EXTRACTO", "Banco"),
        "A-CONTABLE", fecha(1),
    )

    contrato = nucleo.registrar_evidencia(Evidencia(
        evidencia_id="E-CONTRATO",
        fuente_id="F-CONTRATO",
        tipo="CONTRATO",
        referencia="CAS:contrato",
        recibida_en=fecha(2),
        integridad="INTEGRA",
        autenticidad="PRESUMIBLEMENTE_AUTENTICA",
        veracidad="NO_VALORADA",
    ), "A-CONTABLE")

    extracto = nucleo.registrar_evidencia(Evidencia(
        evidencia_id="E-EXTRACTO",
        fuente_id="F-BANCO",
        tipo="EXTRACTO",
        referencia="CAS:extracto",
        recibida_en=fecha(18),
        integridad="INTEGRA",
        autenticidad="AUTENTICA",
        veracidad="COHERENTE",
    ), "A-CONTABLE")

    hecho = nucleo.registrar_hecho(HechoEconomico(
        hecho_id="H-SERVICIO",
        entidad_id="EMP-A",
        tipo="EJECUCION_SERVICIO",
        descripcion="Servicio ejecutado el 31 de marzo",
        ocurrido=FechaEconomica(TipoFecha.EXACTA, inicio=datetime(2025, 3, 31)),
        conocido_en=fecha(10),
        registrado_en=fecha(10),
        estado_economico="EJECUTADO",
        magnitudes=(Magnitud("IMPORTE_ACORDADO", 121000),),
    ), "A-CONTABLE")

    nucleo.asociar_evidencia(
        "H-SERVICIO", "E-CONTRATO", "SUSTENTA",
        "El contrato sustenta la obligación",
        "A-CONTABLE", fecha(10),
    )

    criterio = nucleo.registrar_criterio(Criterio(
        criterio_id="C-DEVENGO",
        categoria="PRINCIPIO_CONTABLE",
        nombre="Devengo económico",
        fundamento="El servicio se ejecuta antes de la factura",
        version="POC-1",
        vigente_desde=datetime(2025, 1, 1),
    ), "A-CONTABLE")

    nucleo.proponer_interpretacion(Interpretacion(
        interpretacion_id="I-DEVENGO",
        hecho_id="H-SERVICIO",
        tipo="CONTABLE",
        descripcion="Reconocimiento al completar el servicio",
        evidencia_ids=("E-CONTRATO",),
        criterio_ids=(criterio.criterio_id,),
        incertidumbre=None,
        propuesta_por="A-CONTABLE",
        propuesta_en=fecha(11),
    ), "A-CONTABLE")

    nucleo.proponer_interpretacion(Interpretacion(
        interpretacion_id="I-FACTURA",
        hecho_id="H-SERVICIO",
        tipo="ALTERNATIVA",
        descripcion="Esperar a la factura para reconocer",
        evidencia_ids=("E-CONTRATO",),
        criterio_ids=(criterio.criterio_id,),
        incertidumbre=None,
        propuesta_por="A-CONTABLE",
        propuesta_en=fecha(11),
    ), "A-CONTABLE")

    autorizacion = nucleo.otorgar_autorizacion(Autorizacion(
        autorizacion_id="AUT-1",
        actor_id="A-AUTORIDAD",
        competencia="APROBAR_RECONOCIMIENTO",
        alcance="Reconocimiento económico inicial",
        otorgada_en=fecha(12),
    ))

    decision = nucleo.adoptar_decision(Decision(
        decision_id="D-DEVENGO",
        objeto_id="H-SERVICIO",
        interpretacion_adoptada_id="I-DEVENGO",
        interpretaciones_descartadas=("I-FACTURA",),
        criterio_ids=("C-DEVENGO",),
        evidencia_ids=("E-CONTRATO",),
        motivo="El contrato y la ejecución acreditada justifican el devengo",
        actor_id="A-CONTABLE",
        autorizacion_id=autorizacion.autorizacion_id,
        decidida_en=fecha(12),
    ))

    nucleo.interpretaciones["I-FACTURA"].estado = nucleo.interpretaciones["I-FACTURA"].estado.DESCARTADA

    representacion = nucleo.crear_representacion(RepresentacionContable(
        representacion_id="R-1",
        hecho_ids=("H-SERVICIO",),
        interpretacion_id="I-DEVENGO",
        decision_id="D-DEVENGO",
        criterio_ids=("C-DEVENGO",),
        marco="PGC_ES",
        fecha_contable=fecha(12),
        lineas=(Linea("430", debe=121000), Linea("705", haber=121000)),
    ), "A-CONTABLE")

    nucleo.asociar_evidencia(
        "H-SERVICIO", "E-EXTRACTO", "CUANTIFICA",
        "El extracto acredita un cobro parcial",
        "A-CONTABLE", fecha(18),
    )

    representacion_rectificada = nucleo.crear_representacion(RepresentacionContable(
        representacion_id="R-2",
        hecho_ids=("H-SERVICIO",),
        interpretacion_id="I-DEVENGO",
        decision_id="D-DEVENGO",
        criterio_ids=("C-DEVENGO",),
        marco="PGC_ES",
        fecha_contable=fecha(18),
        lineas=(Linea("572", debe=50000), Linea("430", haber=50000)),
    ), "A-CONTABLE")

    nucleo.crear_rectificacion(Rectificacion(
        rectificacion_id="X-1",
        representacion_original_id="R-1",
        representacion_nueva_id="R-2",
        tipo="RECTIFICACION_PARCIAL",
        causa="COBRO_PARCIAL",
        motivo="Se acredita cobro parcial de 500 euros",
        actor_id="A-CONTABLE",
        autorizacion_id="AUT-1",
        creada_en=fecha(18),
    ), "A-CONTABLE")

    return nucleo


def test_vertical_slice_basico():
    nucleo = construir_vertical_slice()
    assert len(nucleo.hechos) == 1
    assert len(nucleo.evidencias) == 2
    assert len(nucleo.interpretaciones) == 2
    assert nucleo.representaciones["R-1"].cuadra()
    assert nucleo.representaciones["R-2"].cuadra()
    assert nucleo.representaciones["R-1"].estado.value == "RECTIFICADA"


def test_evidencia_no_acredita_automaticamente():
    nucleo = construir_vertical_slice()
    hecho = nucleo.hechos["H-SERVICIO"]
    assert hecho.estado_epistemologico.value == "NO_ACREDITADO"


def test_reconstruccion_temporal():
    nucleo = construir_vertical_slice()
    anterior = nucleo.reconstruir(fecha(11))
    posterior = nucleo.reconstruir(fecha(18))
    assert anterior["evidencias"]
    assert posterior["eventos_disponibles"] >= anterior["eventos_disponibles"]


def test_cadena_integridad():
    nucleo = construir_vertical_slice()
    resultado = nucleo.verificar_cadena()
    assert resultado["cadena_valida"]
    assert resultado["total"] == len(nucleo.eventos)


def test_asiento_descuadrado_falla():
    nucleo = construir_vertical_slice()
    try:
        nucleo.crear_representacion(RepresentacionContable(
            representacion_id="R-MALA",
            hecho_ids=("H-SERVICIO",),
            interpretacion_id="I-DEVENGO",
            decision_id="D-DEVENGO",
            criterio_ids=("C-DEVENGO",),
            marco="PGC_ES",
            fecha_contable=fecha(19),
            lineas=(Linea("430", debe=100), Linea("705", haber=90)),
        ), "A-CONTABLE")
    except ErrorDominio:
        return
    raise AssertionError("Debe rechazar asiento descuadrado")
