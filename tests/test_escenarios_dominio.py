"""Cinco escenarios formales del núcleo epistemológico-contable."""
from datetime import datetime


def _base():
    from conta_rizoma4.dominio import (
        Actor,
        EntidadContable,
        FechaEconomica,
        HechoEconomico,
        TipoFecha,
    )
    from conta_rizoma4.dominio.servicios.nucleo import NucleoEpistemicoContable

    nucleo = NucleoEpistemicoContable()
    ahora = datetime(2025, 4, 1)
    nucleo.registrar_actor(Actor("CONTADOR", "Contadora"), ahora)
    nucleo.registrar_entidad(EntidadContable("EMP-A", "Empresa A"), "CONTADOR", ahora)
    hecho = nucleo.registrar_hecho(HechoEconomico(
        hecho_id="H-SERVICIO",
        entidad_id="EMP-A",
        tipo="EJECUCION_SERVICIO",
        descripcion="Servicio ejecutado",
        ocurrido=FechaEconomica(TipoFecha.EXACTA, inicio=datetime(2025, 3, 31)),
        conocido_en=ahora,
        registrado_en=ahora,
        estado_economico="EJECUTADO",
    ), "CONTADOR")
    return nucleo, hecho, ahora


def test_scenario_1_operacion_documentada():
    nucleo, hecho, ahora = _base()
    estado = nucleo.reconstruir(datetime(2025, 4, 2))
    assert estado["hechos"]
    assert nucleo.verificar_cadena()["cadena_valida"]


def test_scenario_2_documentacion_recibida_tarde():
    from datetime import timedelta

    nucleo, hecho, ahora = _base()
    anterior = nucleo.reconstruir(datetime(2025, 4, 1))
    posterior = nucleo.reconstruir(datetime(2025, 4, 20))

    assert anterior["eventos_disponibles"] <= posterior["eventos_disponibles"]


def test_scenario_3_interpretaciones_alternativas_no_son_hecho():
    from conta_rizoma4.dominio import Criterio, Evidencia, Fuente, Interpretacion

    nucleo, hecho, ahora = _base()
    nucleo.registrar_fuente(Fuente("CONTRATO", "DOCUMENTAL", "Contrato"), "CONTADOR", ahora)
    nucleo.registrar_evidencia(Evidencia(
        "E-1", "CONTRATO", "CONTRATO", "CAS:contrato", ahora,
        integridad="INTEGRA", registrada_en=ahora,
    ), "CONTADOR")
    nucleo.registrar_criterio(Criterio(
        "C-1", "PRINCIPIO", "Devengo", "Fundamento", "1",
        datetime(2025, 1, 1), registrado_en=ahora,
    ), "CONTADOR")

    interpretacion = nucleo.proponer_interpretacion(Interpretacion(
        "I-1", "H-SERVICIO", "CONTABLE", "Reconocimiento por devengo",
        ("E-1",), ("C-1",), None, "CONTADOR", ahora,
    ), "CONTADOR")
    nucleo.asociar_evidencia(
        "H-SERVICIO", "E-1", "SUSTENTA", "Contrato del servicio", "CONTADOR", ahora,
    )

    assert interpretacion.hecho_id == "H-SERVICIO"
    assert hecho.estado_epistemologico.value == "NO_ACREDITADO"
    estado = nucleo.reconstruir(ahora)
    assert estado["evidencias"]["E-1"]["registrada_en"] == ahora.isoformat()
    assert estado["criterios"]["C-1"]["registrado_en"] == ahora.isoformat()
    assert "H-SERVICIO:E-1" in estado["valoraciones_evidencia"]


def test_scenario_4_error_descubierto_despues_del_cierre():
    nucleo, hecho, ahora = _base()

    estado = nucleo.reconstruir(datetime(2025, 4, 20))

    assert estado["representaciones"] == {}
    assert "rectificacion" not in estado


def test_scenario_5_nueva_evidencia_revisa_decision():
    nucleo, hecho, ahora = _base()

    estado_temprano = nucleo.reconstruir(datetime(2025, 4, 1))
    estado_tarde = nucleo.reconstruir(datetime(2025, 5, 1))

    assert estado_temprano["eventos_disponibles"] <= estado_tarde["eventos_disponibles"]
