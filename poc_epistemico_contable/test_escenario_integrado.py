"""Escenario completo integrado con el primer lote migrado."""
from datetime import datetime

from .lote1 import generar_lote1
from .modelo import (
    Actor,
    Autorizacion,
    Criterio,
    Decision,
    EntidadContable,
    Evidencia,
    FechaEconomica,
    Fuente,
    HechoEconomico,
    Interpretacion,
    Linea,
    Rectificacion,
    RepresentacionContable,
    TipoFecha,
)
from .nucleo import NucleoEpistemicoContable


def fecha(dia: int) -> datetime:
    return datetime(2025, 4, dia)


def construir_escenario_completo():
    nucleo = NucleoEpistemicoContable()

    nucleo.registrar_actor(Actor("CONTADOR", "Contadora"), fecha(1))
    nucleo.registrar_actor(Actor("AUTORIZADOR", "Responsable económico"), fecha(1))
    nucleo.registrar_entidad(EntidadContable("EMP-A", "Empresa A"), "CONTADOR", fecha(1))

    nucleo.registrar_fuente(Fuente("CLIENTE", "TERCERO", "Empresa cliente"),
                           "CONTADOR", fecha(2))
    nucleo.registrar_fuente(Fuente("CONTRATO", "DOCUMENTAL", "Contrato de prestación"),
                           "CONTADOR", fecha(2))
    nucleo.registrar_fuente(Fuente("BANCO", "EXTRACTO", "Entidad bancaria"),
                           "CONTADOR", fecha(2))

    contrato = nucleo.registrar_evidencia(Evidencia(
        "E-CONTRATO", "CONTRATO", "CONTRATO", "CAS:contrato", fecha(2),
        integridad="INTEGRA", autenticidad="AUTENTICA", veracidad="COHERENTE",
    ), "CONTADOR")
    factura_evidencia = nucleo.registrar_evidencia(Evidencia(
        "E-FACTURA", "CLIENTE", "FACTURA", "CAS:factura", fecha(12),
        integridad="INTEGRA", autenticidad="PRESUMIBLEMENTE_AUTENTICA",
        veracidad="NO_VALORADA",
    ), "CONTADOR")
    extracto = nucleo.registrar_evidencia(Evidencia(
        "E-EXTRACTO", "BANCO", "EXTRACTO", "CAS:extracto", fecha(18),
        integridad="INTEGRA", autenticidad="AUTENTICA", veracidad="COHERENTE",
    ), "CONTADOR")

    hecho = nucleo.registrar_hecho(HechoEconomico(
        hecho_id="H-SERVICIO",
        entidad_id="EMP-A",
        tipo="EJECUCION_SERVICIO",
        descripcion="Servicio ejecutado; importe inicialmente controvertido",
        ocurrido=FechaEconomica(TipoFecha.EXACTA, inicio=datetime(2025, 3, 31)),
        conocido_en=fecha(10),
        registrado_en=fecha(10),
        estado_economico="EJECUTADO",
        magnitudes=(),
    ), "CONTADOR")

    nucleo.asociar_evidencia("H-SERVICIO", "E-CONTRATO", "SUSTENTA",
                             "Contrato confirma ejecución contractual",
                             "CONTADOR", fecha(10))

    criterio = nucleo.registrar_criterio(Criterio(
        "C-DEVENGO", "PRINCIPIO_CONTABLE", "Devengo económico",
        "El servicio ejecutado genera reconocimiento", "1.0",
        datetime(2025, 1, 1),
    ), "CONTADOR")

    nucleo.proponer_interpretacion(Interpretacion(
        "I-DEVENGO", "H-SERVICIO", "CONTABLE",
        "Reconocer el derecho completo al finalizar el servicio",
        ("E-CONTRATO",), ("C-DEVENGO",), None,
        "CONTADOR", fecha(11),
    ), "CONTADOR")

    nucleo.proponer_interpretacion(Interpretacion(
        "I-FACTURA", "H-SERVICIO", "ALTERNATIVA",
        "Esperar a factura definitiva antes de reconocer",
        ("E-CONTRATO",), ("C-DEVENGO",), None,
        "CONTADOR", fecha(11),
    ), "CONTADOR")

    autorizacion = nucleo.otorgar_autorizacion(Autorizacion(
        "AUT-DEVENGO", "AUTORIZADOR", "APROBAR_ASIENTO",
        "Reconocimiento inicial", fecha(12),
    ))

    decision = nucleo.adoptar_decision(Decision(
        "D-DEVENGO", "H-SERVICIO", "I-DEVENGO", ("I-FACTURA",),
        ("C-DEVENGO",), ("E-CONTRATO",),
        "El contrato y la ejecución justifican reconocimiento provisional",
        "CONTADOR", autorizacion.autorizacion_id, fecha(12),
    ))

    nucleo.interpretaciones["I-FACTURA"].estado = nucleo.interpretaciones["I-FACTURA"].estado.DESCARTADA

    factura = generar_lote1(
        "A_FACT_EMIT_SERV_NAC_SIN_RET",
        base_centimos=100000,
        iva_pct=21,
        cliente_nif="B123",
    )
    lineas_factura = tuple(
        Linea(cuenta, debe, haber) for cuenta, debe, haber in factura.lineas
    )

    representacion_factura = nucleo.crear_representacion(RepresentacionContable(
        "R-FACTURA", ("H-SERVICIO",), "I-DEVENGO", "D-DEVENGO",
        ("C-DEVENGO",), "PGC_ES", fecha(12), lineas_factura,
    ), "CONTADOR")

    cobro = generar_lote1(
        "A_COBRO_CLIENTE_TRANSF",
        importe_centimos=50000,
        cliente_nif="B123",
    )
    lineas_cobro = tuple(
        Linea(cuenta, debe, haber) for cuenta, debe, haber in cobro.lineas
    )

    nucleo.asociar_evidencia("H-SERVICIO", "E-FACTURA", "CUANTIFICA",
                             "La factura cuantifica el importe", "CONTADOR", fecha(12))
    nucleo.asociar_evidencia("H-SERVICIO", "E-EXTRACTO", "CORROBORA",
                             "El extracto acredita el cobro parcial", "CONTADOR", fecha(18))

    representacion_cobro = nucleo.crear_representacion(RepresentacionContable(
        "R-COBRO", ("H-SERVICIO",), "I-DEVENGO", "D-DEVENGO",
        ("C-DEVENGO",), "PGC_ES", fecha(18), lineas_cobro,
    ), "CONTADOR")

    nucleo.crear_rectificacion(Rectificacion(
        "X-COBRO", "R-FACTURA", "R-COBRO", "COBRO_PARCIAL",
        "NUEVA_EVIDENCIA", "El cobro reduce el derecho pendiente",
        "CONTADOR", autorizacion.autorizacion_id, fecha(18),
    ), "CONTADOR")

    return nucleo


def test_escenario_integrado_completo():
    nucleo = construir_escenario_completo()

    assert len(nucleo.hechos) == 1
    assert len(nucleo.evidencias) == 3
    assert len(nucleo.interpretaciones) == 2
    assert len(nucleo.representaciones) == 2
    assert len(nucleo.rectificaciones) == 1

    assert nucleo.representaciones["R-FACTURA"].estado.value == "RECTIFICADA"
    assert nucleo.representaciones["R-COBRO"].estado.value == "REGISTRADA"


def test_escenario_reconstruye_antes_y_despues():
    nucleo = construir_escenario_completo()

    antes = nucleo.reconstruir(datetime(2025, 4, 11))
    despues = nucleo.reconstruir(datetime(2025, 4, 18))

    assert antes["eventos_disponibles"] < despues["eventos_disponibles"]
    assert "E-FACTURA" not in antes["evidencias"]
    assert "E-FACTURA" in despues["evidencias"]


def test_escenario_ledger_valido():
    nucleo = construir_escenario_completo()
    resultado = nucleo.verificar_cadena()
    assert resultado["cadena_valida"]
    assert resultado["roturas"] == []
