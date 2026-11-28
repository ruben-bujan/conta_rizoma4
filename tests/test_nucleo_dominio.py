"""Prueba del núcleo formal promovido con el vertical slice básico."""
from datetime import datetime

import pytest


def test_nucleo_formal_registra_y_verifica():
    from conta_rizoma4.dominio.servicios.nucleo import NucleoEpistemicoContable
    from conta_rizoma4.dominio import (
        Actor,
        EntidadContable,
        FechaEconomica,
        HechoEconomico,
        TipoFecha,
    )

    nucleo = NucleoEpistemicoContable()
    ahora = datetime(2025, 4, 1)

    nucleo.registrar_actor(Actor("CONTADOR", "Contadora"), ahora)
    nucleo.registrar_entidad(EntidadContable("EMP-A", "Empresa A"), "CONTADOR", ahora)

    hecho = nucleo.registrar_hecho(HechoEconomico(
        hecho_id="H-1",
        entidad_id="EMP-A",
        tipo="EJECUCION_SERVICIO",
        descripcion="Servicio ejecutado",
        ocurrido=FechaEconomica(TipoFecha.EXACTA, inicio=datetime(2025, 3, 31)),
        conocido_en=ahora,
        registrado_en=ahora,
        estado_economico="EJECUTADO",
    ), "CONTADOR")

    reconstruccion = nucleo.reconstruir(datetime(2025, 4, 2))
    integridad = nucleo.verificar_cadena()

    assert hecho.hecho_id == "H-1"
    assert reconstruccion["eventos_disponibles"] == 3
    assert integridad["cadena_valida"]


def test_nucleo_formal_rechaza_transicion_invalida():
    from conta_rizoma4.dominio.servicios.nucleo import NucleoEpistemicoContable
    from conta_rizoma4.dominio import (
        Actor,
        EntidadContable,
        EstadoEpistemologico,
        FechaEconomica,
        HechoEconomico,
        TipoFecha,
    )
    from conta_rizoma4.dominio import ErrorDominio

    nucleo = NucleoEpistemicoContable()
    ahora = datetime(2025, 4, 1)
    nucleo.registrar_actor(Actor("CONTADOR", "Contadora"), ahora)
    nucleo.registrar_entidad(EntidadContable("EMP-A", "Empresa A"), "CONTADOR", ahora)
    nucleo.registrar_hecho(HechoEconomico(
        hecho_id="H-1",
        entidad_id="EMP-A",
        tipo="EJECUCION_SERVICIO",
        descripcion="Servicio ejecutado",
        ocurrido=FechaEconomica(TipoFecha.EXACTA, inicio=datetime(2025, 3, 31)),
        conocido_en=ahora,
        registrado_en=ahora,
        estado_economico="EJECUTADO",
    ), "CONTADOR")

    try:
        nucleo.cambiar_estado_epistemologico(
            "H-1",
            EstadoEpistemologico.ACREDITADO,
            "CONTADOR",
            datetime(2025, 4, 2),
            "Intento sin declaración previa",
        )
    except ErrorDominio:
        return

    raise AssertionError("Debe rechazar transición epistemológica inválida")


def test_reconstruccion_usa_estado_del_hecho_vigente_en_la_fecha():
    from conta_rizoma4.dominio import (
        Actor, EntidadContable, EstadoEpistemologico, FechaEconomica,
        HechoEconomico, TipoFecha,
    )
    from conta_rizoma4.dominio.servicios.nucleo import NucleoEpistemicoContable

    nucleo = NucleoEpistemicoContable()
    antes = datetime(2025, 4, 1)
    despues = datetime(2025, 4, 2)
    nucleo.registrar_actor(Actor("CONTADOR", "Contadora"), antes)
    nucleo.registrar_entidad(EntidadContable("EMP-A", "Empresa A"), "CONTADOR", antes)
    nucleo.registrar_hecho(HechoEconomico(
        hecho_id="H-1", entidad_id="EMP-A", tipo="SERVICIO",
        descripcion="Servicio", ocurrido=FechaEconomica(TipoFecha.EXACTA, inicio=antes),
        conocido_en=antes, registrado_en=antes, estado_economico="EJECUTADO",
    ), "CONTADOR")

    nucleo.cambiar_estado_epistemologico(
        "H-1", EstadoEpistemologico.DECLARADO, "CONTADOR", despues, "Declaración recibida",
    )

    estado_antes = nucleo.reconstruir(antes)
    estado_despues = nucleo.reconstruir(despues)
    assert estado_antes["hechos"][0]["estado_epistemologico"] == "NO_ACREDITADO"
    assert estado_despues["hechos"][0]["estado_epistemologico"] == "DECLARADO"


def test_hash_del_evento_cubre_estado_anterior_y_posterior():
    from conta_rizoma4.dominio import Actor
    from conta_rizoma4.dominio.servicios.nucleo import NucleoEpistemicoContable

    nucleo = NucleoEpistemicoContable()
    nucleo.registrar_actor(Actor("CONTADOR", "Contadora"), datetime(2025, 4, 1))
    assert nucleo.verificar_cadena()["cadena_valida"]

    nucleo.eventos[0].estado_posterior["nombre"] = "Alterado"
    resultado = nucleo.verificar_cadena()
    assert not resultado["cadena_valida"]
    assert any(rotura["tipo"] == "huella" for rotura in resultado["roturas"])


def test_propuesta_de_interpretacion_exige_actor_registrado():
    import pytest
    from conta_rizoma4.dominio import (
        Actor, EntidadContable, ErrorDominio, FechaEconomica,
        HechoEconomico, Interpretacion, TipoFecha,
    )
    from conta_rizoma4.dominio.servicios.nucleo import NucleoEpistemicoContable

    nucleo = NucleoEpistemicoContable()
    ahora = datetime(2025, 4, 1)
    nucleo.registrar_actor(Actor("CONTADOR", "Contadora"), ahora)
    nucleo.registrar_entidad(EntidadContable("EMP-A", "Empresa A"), "CONTADOR", ahora)
    nucleo.registrar_hecho(HechoEconomico(
        hecho_id="H-1", entidad_id="EMP-A", tipo="SERVICIO",
        descripcion="Servicio", ocurrido=FechaEconomica(TipoFecha.EXACTA, inicio=ahora),
        conocido_en=ahora, registrado_en=ahora, estado_economico="EJECUTADO",
    ), "CONTADOR")

    with pytest.raises(ErrorDominio, match="Actor inexistente"):
        nucleo.proponer_interpretacion(Interpretacion(
            "I-1", "H-1", "CONTABLE", "Interpretación", (), (), None,
            "FALSO-ACTOR", ahora,
        ), "FALSO-ACTOR")


def test_reconstruccion_no_anticipa_adopcion_de_interpretacion():
    from conta_rizoma4.dominio import (
        Actor, Autorizacion, Decision, EntidadContable, FechaEconomica,
        HechoEconomico, Interpretacion, Rol, TipoFecha,
    )
    from conta_rizoma4.dominio.servicios.nucleo import NucleoEpistemicoContable

    nucleo = NucleoEpistemicoContable()
    propuesta_en = datetime(2025, 4, 2)
    decision_en = datetime(2025, 4, 3)
    nucleo.registrar_actor(
        Actor("CONTADOR", "Contadora", rol=Rol.JEFE_CONTABILIDAD), datetime(2025, 4, 1),
    )
    nucleo.registrar_entidad(
        EntidadContable("EMP-A", "Empresa A"), "CONTADOR", datetime(2025, 4, 1),
    )
    nucleo.registrar_hecho(HechoEconomico(
        hecho_id="H-1", entidad_id="EMP-A", tipo="SERVICIO",
        descripcion="Servicio", ocurrido=FechaEconomica(
            TipoFecha.EXACTA, inicio=datetime(2025, 4, 1),
        ), conocido_en=datetime(2025, 4, 1), registrado_en=datetime(2025, 4, 1),
        estado_economico="EJECUTADO",
    ), "CONTADOR")
    nucleo.proponer_interpretacion(Interpretacion(
        "I-1", "H-1", "CONTABLE", "Reconocimiento por devengo", (), (), None,
        "CONTADOR", propuesta_en,
    ), "CONTADOR")
    nucleo.proponer_interpretacion(Interpretacion(
        "I-2", "H-1", "CONTABLE", "Reconocimiento alternativo", (), (), None,
        "CONTADOR", propuesta_en,
    ), "CONTADOR")
    nucleo.registrar_actor(Actor("AUTORIZADOR", "Autorizador"), propuesta_en)
    nucleo.otorgar_autorizacion(Autorizacion(
        "A-1", "AUTORIZADOR", "ADOPTAR_DECISION", "H-1", propuesta_en,
    ))
    nucleo.adoptar_decision(Decision(
        "D-1", "H-1", "I-1", ("I-2",), (), (), "Criterio adoptado", "CONTADOR",
        "A-1", decision_en,
    ))

    antes = nucleo.reconstruir(datetime(2025, 4, 2, 23, 59))
    despues = nucleo.reconstruir(datetime(2025, 4, 4))
    assert antes["interpretaciones"]["I-1"]["estado"] == "PROPUESTA"
    assert antes["interpretaciones"]["I-2"]["estado"] == "PROPUESTA"
    assert "D-1" not in antes["decisiones"]
    assert despues["interpretaciones"]["I-1"]["estado"] == "ADOPTADA"
    assert despues["interpretaciones"]["I-2"]["estado"] == "DESCARTADA"
    assert despues["decisiones"]["D-1"]["estado"] == "ADOPTADA"


def test_reconstruccion_separa_fecha_contable_y_fecha_de_registro_de_representacion():
    from conta_rizoma4.dominio import (
        Actor, Autorizacion, Decision, EntidadContable, FechaEconomica,
        HechoEconomico, Interpretacion, Linea, RepresentacionContable,
        Rol, TipoFecha,
    )
    from conta_rizoma4.dominio.servicios.nucleo import NucleoEpistemicoContable

    nucleo = NucleoEpistemicoContable()
    conocida = datetime(2025, 4, 1)
    contable = datetime(2025, 3, 31)
    registrada = datetime(2025, 4, 3)
    nucleo.registrar_actor(
        Actor("CONTADOR", "Contadora", rol=Rol.JEFE_CONTABILIDAD), conocida,
    )
    nucleo.registrar_entidad(EntidadContable("EMP-A", "Empresa A"), "CONTADOR", conocida)
    nucleo.registrar_hecho(HechoEconomico(
        hecho_id="H-1", entidad_id="EMP-A", tipo="SERVICIO",
        descripcion="Servicio", ocurrido=FechaEconomica(TipoFecha.EXACTA, inicio=contable),
        conocido_en=conocida, registrado_en=conocida, estado_economico="EJECUTADO",
    ), "CONTADOR")
    nucleo.proponer_interpretacion(Interpretacion(
        "I-1", "H-1", "CONTABLE", "Reconocimiento", (), (), None,
        "CONTADOR", conocida,
    ), "CONTADOR")
    nucleo.registrar_actor(Actor("AUTORIZADOR", "Autorizador"), conocida)
    nucleo.otorgar_autorizacion(Autorizacion(
        "A-1", "AUTORIZADOR", "ADOPTAR_DECISION", "H-1", conocida,
    ))
    nucleo.adoptar_decision(Decision(
        "D-1", "H-1", "I-1", (), (), (), "Decisión", "CONTADOR",
        "A-1", datetime(2025, 4, 2),
    ))
    representacion = RepresentacionContable(
        "R-1", ("H-1",), "I-1", "D-1", (), "PGC_PYMES", contable,
        (Linea("600", debe=100), Linea("400", haber=100)),
        "A-1", registrada_en=registrada,
    )
    nucleo.crear_representacion(representacion, "CONTADOR")

    antes_del_registro = nucleo.reconstruir(datetime(2025, 4, 2, 23, 59))
    despues_del_registro = nucleo.reconstruir(datetime(2025, 4, 3))
    assert antes_del_registro["representaciones"] == {}
    assert despues_del_registro["representaciones"]["R-1"]["fecha_contable"] == contable.isoformat()
    assert despues_del_registro["representaciones"]["R-1"]["registrada_en"] == registrada.isoformat()


def test_adoptar_decision_rechaza_operario_por_matriz():
    import pytest
    from conta_rizoma4.dominio import (
        Actor, Autorizacion, Decision, EntidadContable, ErrorDominio,
        FechaEconomica, HechoEconomico, Interpretacion, Rol, TipoFecha,
    )
    from conta_rizoma4.dominio.servicios.nucleo import NucleoEpistemicoContable

    nucleo = NucleoEpistemicoContable()
    ahora = datetime(2025, 4, 1)
    nucleo.registrar_actor(Actor("OP", "Operario", rol=Rol.OPERARIO), ahora)
    nucleo.registrar_entidad(EntidadContable("EMP-A", "Empresa A"), "OP", ahora)
    nucleo.registrar_hecho(HechoEconomico(
        hecho_id="H-1", entidad_id="EMP-A", tipo="SERVICIO",
        descripcion="Servicio", ocurrido=FechaEconomica(TipoFecha.EXACTA, inicio=ahora),
        conocido_en=ahora, registrado_en=ahora, estado_economico="EJECUTADO",
    ), "OP")
    nucleo.proponer_interpretacion(Interpretacion(
        "I-1", "H-1", "CONTABLE", "Reconocimiento", (), (), None, "OP", ahora,
    ), "OP")
    nucleo.registrar_actor(Actor("AUTORIZADOR", "Autorizador"), ahora)
    nucleo.otorgar_autorizacion(Autorizacion(
        "A-1", "AUTORIZADOR", "ADOPTAR_DECISION", "H-1", ahora,
    ))

    with pytest.raises(ErrorDominio, match="no tiene competencia"):
        nucleo.adoptar_decision(Decision(
            "D-1", "H-1", "I-1", (), (), (), "Decisión", "OP", "A-1", ahora,
        ))


def test_crear_representacion_exige_jefe_y_permiso_de_asiento():
    import pytest
    from conta_rizoma4.dominio import (
        Actor, Autorizacion, Decision, EntidadContable, ErrorDominio,
        FechaEconomica, HechoEconomico, Interpretacion, Linea,
        RepresentacionContable, Rol, TipoFecha,
    )
    from conta_rizoma4.dominio.servicios.nucleo import NucleoEpistemicoContable

    nucleo = NucleoEpistemicoContable()
    ahora = datetime(2025, 4, 1)
    decision_en = datetime(2025, 4, 2)
    registrada_en = datetime(2025, 4, 4)
    nucleo.registrar_actor(Actor("DIR", "Directora", rol=Rol.DIRECTOR), ahora)
    nucleo.registrar_actor(
        Actor("JEFE", "Jefe", rol=Rol.JEFE_CONTABILIDAD), ahora,
    )
    nucleo.registrar_actor(Actor("OP", "Operario", rol=Rol.OPERARIO), ahora)
    nucleo.registrar_actor(Actor("AUTORIZADOR", "Autorizador"), ahora)
    nucleo.registrar_entidad(EntidadContable("EMP-A", "Empresa A"), "JEFE", ahora)
    nucleo.registrar_hecho(HechoEconomico(
        hecho_id="H-1", entidad_id="EMP-A", tipo="SERVICIO",
        descripcion="Servicio", ocurrido=FechaEconomica(TipoFecha.EXACTA, inicio=ahora),
        conocido_en=ahora, registrado_en=ahora, estado_economico="EJECUTADO",
    ), "JEFE")
    nucleo.proponer_interpretacion(Interpretacion(
        "I-1", "H-1", "CONTABLE", "Reconocimiento", (), (), None, "JEFE", ahora,
    ), "JEFE")
    nucleo.otorgar_autorizacion(Autorizacion(
        "A-DEC", "AUTORIZADOR", "ADOPTAR_DECISION", "H-1", ahora,
    ))
    nucleo.adoptar_decision(Decision(
        "D-1", "H-1", "I-1", (), (), (), "Decisión", "JEFE", "A-DEC", decision_en,
    ))
    nucleo.otorgar_autorizacion(Autorizacion(
        "A-REP", "AUTORIZADOR", "REGISTRAR_REPRESENTACION", "H-1",
        datetime(2025, 4, 3),
    ))
    representacion = RepresentacionContable(
        "R-1", ("H-1",), "I-1", "D-1", (), "PGC_PYMES", ahora,
        (Linea("600", debe=100), Linea("400", haber=100)),
        "A-REP", registrada_en=registrada_en,
    )

    with pytest.raises(ErrorDominio, match="REPRESENTACION"):
        nucleo.crear_representacion(representacion, "OP")

    nucleo.conceder_permiso(
        "P-REP", "DIR", "OP", "REPRESENTACION", "*", datetime(2025, 4, 3),
    )
    with pytest.raises(ErrorDominio, match="ASIENTO_DIARIO"):
        nucleo.crear_representacion(representacion, "OP")


def test_adopcion_rechaza_autorizacion_fuera_de_alcance_sin_mutar_estado():
    import pytest
    from conta_rizoma4.dominio import (
        Actor, Autorizacion, Decision, EntidadContable, ErrorDominio,
        FechaEconomica, HechoEconomico, Interpretacion, Rol, TipoFecha,
    )
    from conta_rizoma4.dominio.servicios.nucleo import NucleoEpistemicoContable

    nucleo = NucleoEpistemicoContable()
    ahora = datetime(2025, 4, 1)
    decision_en = datetime(2025, 4, 3)
    nucleo.registrar_actor(
        Actor("DECISOR", "Decisor", rol=Rol.JEFE_CONTABILIDAD), ahora,
    )
    nucleo.registrar_actor(Actor("AUTORIZADOR", "Autorizador"), ahora)
    nucleo.registrar_entidad(EntidadContable("EMP-A", "Empresa A"), "DECISOR", ahora)
    nucleo.registrar_hecho(HechoEconomico(
        hecho_id="H-1", entidad_id="EMP-A", tipo="SERVICIO",
        descripcion="Servicio", ocurrido=FechaEconomica(TipoFecha.EXACTA, inicio=ahora),
        conocido_en=ahora, registrado_en=ahora, estado_economico="EJECUTADO",
    ), "DECISOR")
    nucleo.proponer_interpretacion(Interpretacion(
        "I-1", "H-1", "CONTABLE", "Reconocimiento", (), (), None,
        "DECISOR", ahora,
    ), "DECISOR")
    nucleo.otorgar_autorizacion(Autorizacion(
        "A-1", "AUTORIZADOR", "ADOPTAR_DECISION", "OTRO-OBJETO", ahora,
    ))

    with pytest.raises(ErrorDominio, match="no cubre"):
        nucleo.adoptar_decision(Decision(
            "D-1", "H-1", "I-1", (), (), (), "Decidir", "DECISOR",
            "A-1", decision_en,
        ))

    assert "D-1" not in nucleo.decisiones
    assert nucleo.interpretaciones["I-1"].estado.value == "PROPUESTA"


def test_ledger_rechaza_fecha_regresiva_antes_de_mutar_estado():
    import pytest
    from conta_rizoma4.dominio import Actor, EntidadContable, ErrorDominio
    from conta_rizoma4.dominio.servicios.nucleo import NucleoEpistemicoContable

    nucleo = NucleoEpistemicoContable()
    nucleo.registrar_actor(Actor("CONTADOR", "Contadora"), datetime(2025, 4, 2))

    with pytest.raises(ErrorDominio, match="fecha anterior"):
        nucleo.registrar_entidad(
            EntidadContable("EMP-A", "Empresa A"), "CONTADOR", datetime(2025, 4, 1),
        )

    assert "EMP-A" not in nucleo.entidades
    assert len(nucleo.eventos) == 1


def test_revocacion_de_autorizacion_es_un_evento_y_rechaza_no_otorgante():
    import pytest
    from conta_rizoma4.dominio import Actor, Autorizacion, ErrorDominio
    from conta_rizoma4.dominio.servicios.nucleo import NucleoEpistemicoContable

    nucleo = NucleoEpistemicoContable()
    inicio = datetime(2025, 4, 1)
    nucleo.registrar_actor(Actor("OTORGANTE", "Otorgante"), inicio)
    nucleo.registrar_actor(Actor("OTRO", "Otro"), inicio)
    nucleo.otorgar_autorizacion(Autorizacion(
        "A-1", "OTORGANTE", "CIERRE_EJERCICIO", "EJ-25", inicio,
    ))

    with pytest.raises(ErrorDominio, match="Sólo quien otorgó"):
        nucleo.revocar_autorizacion("A-1", "OTRO", "Revocar", datetime(2025, 4, 2))
    assert nucleo.autorizaciones["A-1"].revocada_en is None

    nucleo.revocar_autorizacion("A-1", "OTORGANTE", "Cambio de competencia", datetime(2025, 4, 2))
    antes = nucleo.reconstruir(datetime(2025, 4, 1, 12))
    despues = nucleo.reconstruir(datetime(2025, 4, 3))
    assert antes["autorizaciones"]["A-1"]["revocada_en"] is None
    assert despues["autorizaciones"]["A-1"]["revocada_por"] == "OTORGANTE"


def test_concesión_de_permiso_respeta_cadena_jerarquica():
    from conta_rizoma4.dominio import Actor, ErrorDominio, Rol
    from conta_rizoma4.dominio.servicios.nucleo import NucleoEpistemicoContable

    nucleo = NucleoEpistemicoContable()
    ahora = datetime(2025, 4, 1)
    nucleo.registrar_actor(Actor("DIR", "Director", rol=Rol.DIRECTOR), ahora)
    nucleo.registrar_actor(Actor("SUB", "Subdirector", rol=Rol.SUBDIRECTOR), ahora)
    nucleo.registrar_actor(Actor("JEF", "Jefe", rol=Rol.JEFE_CONTABILIDAD), ahora)

    nucleo.conceder_permiso("P-1", "DIR", "SUB", "CIERRE_EJERCICIO", "EJ-25", ahora)
    nucleo.conceder_permiso("P-2", "SUB", "JEF", "ASIENTO_DIARIO", "EJ-25", ahora)

    with pytest.raises(ErrorDominio, match="Solo un superior"):
        nucleo.conceder_permiso("P-3", "JEF", "DIR", "CIERRE_EJERCICIO", "EJ-25", ahora)

    admin = Actor("ADM", "Admin", rol=Rol.ADMIN)
    nucleo.registrar_actor(admin, ahora)
    with pytest.raises(ErrorDominio, match="ADMIN no puede conceder"):
        nucleo.conceder_permiso("P-4", "ADM", "JEF", "ASIENTO_DIARIO", "EJ-25", ahora)


def test_revocación_de_permiso_solo_por_otorgante():
    from conta_rizoma4.dominio import Actor, ErrorDominio, Rol
    from conta_rizoma4.dominio.servicios.nucleo import NucleoEpistemicoContable

    nucleo = NucleoEpistemicoContable()
    ahora = datetime(2025, 4, 1)
    nucleo.registrar_actor(Actor("DIR", "Director", rol=Rol.DIRECTOR), ahora)
    nucleo.registrar_actor(Actor("SUB", "Subdirector", rol=Rol.SUBDIRECTOR), ahora)
    nucleo.conceder_permiso("P-1", "DIR", "SUB", "CIERRE_EJERCICIO", "EJ-25", ahora)

    with pytest.raises(ErrorDominio, match="Solo quien concedió"):
        nucleo.revocar_permiso("P-1", "SUB", "Revocar", datetime(2025, 4, 2))

    nucleo.revocar_permiso("P-1", "DIR", "Revocar", datetime(2025, 4, 2))
    assert nucleo.permisos["P-1"].revocada_en is not None


def test_revocación_de_permiso_conserva_estado_previo_en_la_cadena():
    from conta_rizoma4.dominio import Actor, Rol
    from conta_rizoma4.dominio.servicios.nucleo import NucleoEpistemicoContable

    nucleo = NucleoEpistemicoContable()
    ahora = datetime(2025, 4, 1)
    nucleo.registrar_actor(Actor("JEF", "Jefe", rol=Rol.JEFE_CONTABILIDAD), ahora)
    nucleo.registrar_actor(Actor("AUX", "Auxiliar de obra", rol=Rol.AUXILIAR), ahora)
    nucleo.conceder_permiso("P-1", "JEF", "AUX", "ASIENTO_DIARIO", "EJ-25", ahora)
    nucleo.revocar_permiso("P-1", "JEF", "Revocación", datetime(2025, 4, 2))

    evento = next(evento for evento in nucleo.eventos if evento.tipo == "PERMISO_REVOCADO")
    assert evento.estado_anterior["revocada_en"] is None
    assert evento.estado_posterior["revocada_en"] == datetime(2025, 4, 2)
    assert evento.estado_anterior["beneficiario_id"] == "AUX"


def test_permiso_delegado_solo_rige_dentro_de_vigencia_y_alcance():
    from conta_rizoma4.dominio import Actor, ErrorDominio, Rol
    from conta_rizoma4.dominio.servicios.nucleo import NucleoEpistemicoContable

    nucleo = NucleoEpistemicoContable()
    nucleo.registrar_actor(
        Actor("JEF", "Jefe", rol=Rol.JEFE_CONTABILIDAD), datetime(2025, 4, 1),
    )
    nucleo.registrar_actor(
        Actor("AUX", "Auxiliar de obra", rol=Rol.AUXILIAR), datetime(2025, 4, 1),
    )
    nucleo.conceder_permiso(
        "P-1", "JEF", "AUX", "ASIENTO_DIARIO", "EJ-25",
        datetime(2025, 4, 2), vigente_hasta=datetime(2025, 4, 5),
    )

    with pytest.raises(ErrorDominio, match="no tiene competencia"):
        nucleo.verificar_competencia("AUX", "ASIENTO_DIARIO", "EJ-25", datetime(2025, 4, 1, 12))
    nucleo.verificar_competencia("AUX", "ASIENTO_DIARIO", "EJ-25", datetime(2025, 4, 3))
    with pytest.raises(ErrorDominio, match="no tiene competencia"):
        nucleo.verificar_competencia("AUX", "ASIENTO_DIARIO", "OTRO-EJ", datetime(2025, 4, 3))
    nucleo.revocar_permiso("P-1", "JEF", "Revocación", datetime(2025, 4, 4))
    with pytest.raises(ErrorDominio, match="no tiene competencia"):
        nucleo.verificar_competencia("AUX", "ASIENTO_DIARIO", "EJ-25", datetime(2025, 4, 5))


def test_reconstrucción_de_permiso_revocado_conserva_la_concesión():
    from conta_rizoma4.dominio import Actor, Rol
    from conta_rizoma4.dominio.servicios.nucleo import NucleoEpistemicoContable

    nucleo = NucleoEpistemicoContable()
    nucleo.registrar_actor(
        Actor("JEF", "Jefe", rol=Rol.JEFE_CONTABILIDAD), datetime(2025, 4, 1),
    )
    nucleo.registrar_actor(
        Actor("AUX", "Auxiliar de obra", rol=Rol.AUXILIAR), datetime(2025, 4, 1),
    )
    nucleo.conceder_permiso("P-1", "JEF", "AUX", "ASIENTO_DIARIO", "EJ-25", datetime(2025, 4, 2))
    nucleo.revocar_permiso("P-1", "JEF", "Cambio de competencia", datetime(2025, 4, 3))

    antes = nucleo.reconstruir(datetime(2025, 4, 1, 12))
    vigente = nucleo.reconstruir(datetime(2025, 4, 2, 12))
    revocado = nucleo.reconstruir(datetime(2025, 4, 4))

    assert "P-1" not in antes["permisos"]
    assert vigente["permisos"]["P-1"]["revocada_en"] is None
    assert revocado["permisos"]["P-1"]["beneficiario_id"] == "AUX"
    assert revocado["permisos"]["P-1"]["otorgante_id"] == "JEF"
    assert revocado["permisos"]["P-1"]["revocada_en"] == "2025-04-03T00:00:00"
    assert revocado["permisos"]["P-1"]["motivo_revocacion"] == "Cambio de competencia"


def test_verificar_competencia_rechaza_sin_permiso():
    from conta_rizoma4.dominio import Actor, ErrorDominio, Rol
    from conta_rizoma4.dominio.servicios.nucleo import NucleoEpistemicoContable

    nucleo = NucleoEpistemicoContable()
    ahora = datetime(2025, 4, 1)
    nucleo.registrar_actor(Actor("OP", "Operario", rol=Rol.OPERARIO), ahora)

    with pytest.raises(ErrorDominio, match="no tiene competencia"):
        nucleo.verificar_competencia("OP", "CIERRE_EJERCICIO", "EJ-25", ahora)


@pytest.mark.parametrize(
    ("competencia", "rol_aprobado"),
    [
        ("DECISION", "JEFE_CONTABILIDAD"),
        ("REPRESENTACION", "JEFE_CONTABILIDAD"),
        ("ASIENTO_DIARIO", "JEFE_CONTABILIDAD"),
        ("RECTIFICACION", "JEFE_CONTABILIDAD"),
        ("CIERRE_EJERCICIO", "SUBDIRECTOR"),
        ("REAPERTURA_EJERCICIO", "SUBDIRECTOR"),
    ],
)
def test_matriz_competencias_exige_rol_aprobado(competencia, rol_aprobado):
    from conta_rizoma4.dominio import Actor, ErrorDominio, Rol
    from conta_rizoma4.dominio.servicios.nucleo import NucleoEpistemicoContable

    nucleo = NucleoEpistemicoContable()
    ahora = datetime(2025, 4, 1)
    nucleo.registrar_actor(Actor("OP", "Operario", rol=Rol.OPERARIO), ahora)
    nucleo.registrar_actor(
        Actor("APROBADO", "Aprobado", rol=Rol[rol_aprobado]), ahora,
    )

    with pytest.raises(ErrorDominio, match="no tiene competencia"):
        nucleo.verificar_competencia("OP", competencia, "EJ-25", ahora)
    nucleo.verificar_competencia("APROBADO", competencia, "EJ-25", ahora)


def test_solo_director_activa_modo_critico():
    from conta_rizoma4.dominio import Actor, ErrorDominio, ModoContabilidad, Rol
    from conta_rizoma4.dominio.servicios.nucleo import NucleoEpistemicoContable

    nucleo = NucleoEpistemicoContable()
    ahora = datetime(2025, 4, 1)
    nucleo.registrar_actor(Actor("ENT", "Entidad"), ahora)
    nucleo.registrar_entidad(__import__("conta_rizoma4.dominio.entidades.economicas", fromlist=["EntidadContable"]).EntidadContable("EMP", "Emp"), "ENT", ahora)
    nucleo.registrar_actor(Actor("SUB", "Sub", rol=Rol.SUBDIRECTOR), ahora)

    with pytest.raises(ErrorDominio, match="Solo el DIRECTOR"):
        nucleo.cambiar_modo_contabilidad("EMP", ModoContabilidad.EXTRAORDINARIO_CRITICO, "SUB", ahora, "Motivo")

    nucleo.registrar_actor(Actor("DIR", "Dir", rol=Rol.DIRECTOR), ahora)
    nucleo.cambiar_modo_contabilidad("EMP", ModoContabilidad.EXTRAORDINARIO_CRITICO, "DIR", ahora, "Motivo")
    assert nucleo.modos_entidad["EMP"] == ModoContabilidad.EXTRAORDINARIO_CRITICO


def test_registro_no_asiento_requiere_jefe_y_visado_subdirector():
    from conta_rizoma4.dominio import Actor, ErrorDominio, Rol
    from conta_rizoma4.dominio.servicios.nucleo import NucleoEpistemicoContable

    nucleo = NucleoEpistemicoContable()
    ahora = datetime(2025, 4, 1)
    nucleo.registrar_actor(Actor("JEF", "Jefe", rol=Rol.JEFE_CONTABILIDAD), ahora)
    nucleo.registrar_actor(Actor("SUB", "Sub", rol=Rol.SUBDIRECTOR), ahora)
    nucleo.registrar_actor(Actor("OP", "Operario", rol=Rol.OPERARIO), ahora)

    with pytest.raises(ErrorDominio, match="Solo el JEFE DE CONTABILIDAD"):
        nucleo.registrar_registro_no_asiento("R-1", "CONFIG", "OP", "SUB", "causa", ahora)

    nucleo.registrar_registro_no_asiento("R-1", "CONFIG", "JEF", "SUB", "causa", ahora)
    assert nucleo.registros_no_asiento["R-1"].visado_por == "SUB"


def test_evaluar_criticidad_importe_escala():
    from conta_rizoma4.dominio.servicios.nucleo import NucleoEpistemicoContable
    from conta_rizoma4.dominio import CriticidadImporte

    nucleo = NucleoEpistemicoContable()
    bi = 100000

    assert nucleo.evaluar_criticidad_importe(20000, bi) == (CriticidadImporte.CRITICA, "DIRECTOR")
    assert nucleo.evaluar_criticidad_importe(14000, bi) == (CriticidadImporte.CUASI_CRITICA, "SUBDIRECTOR")
    assert nucleo.evaluar_criticidad_importe(11000, bi) == (CriticidadImporte.MEDIA, None)
    assert nucleo.evaluar_criticidad_importe(8000, bi) == (CriticidadImporte.BAJA_INFORMATIVA, "DIRECTOR")
    assert nucleo.evaluar_criticidad_importe(5000, bi) == (CriticidadImporte.BAJA_INFORMATIVA, "JEFE_CONTABILIDAD")
    assert nucleo.evaluar_criticidad_importe(3000, bi) == (CriticidadImporte.BAJA_INFORMATIVA, None)


def test_autorizacion_no_admite_vigencia_que_precede_a_su_otorgamiento():
    import pytest
    from conta_rizoma4.dominio import Actor, Autorizacion, ErrorDominio
    from conta_rizoma4.dominio.servicios.nucleo import NucleoEpistemicoContable

    nucleo = NucleoEpistemicoContable()
    inicio = datetime(2025, 4, 1)
    nucleo.registrar_actor(Actor("OTORGANTE", "Otorgante"), inicio)
    with pytest.raises(ErrorDominio, match="vigencia no puede terminar"):
        nucleo.otorgar_autorizacion(Autorizacion(
            "A-1", "OTORGANTE", "CIERRE_EJERCICIO", "EJ-25", inicio,
            vigente_hasta=datetime(2025, 3, 31),
        ))


def test_reconstruccion_cubre_eventos_de_autoridad():
    from conta_rizoma4.dominio import (
        Actor, EntidadContable, FechaEconomica, HechoEconomico,
        ModoContabilidad, Rol, TipoFecha,
    )
    from conta_rizoma4.dominio.servicios.nucleo import NucleoEpistemicoContable

    nucleo = NucleoEpistemicoContable()
    inicio = datetime(2025, 4, 1)
    nucleo.registrar_actor(Actor("DIR", "Director", rol=Rol.DIRECTOR), inicio)
    nucleo.registrar_actor(Actor("SUB", "Subdirector", rol=Rol.SUBDIRECTOR), inicio)
    nucleo.registrar_actor(Actor("JEF", "Jefe", rol=Rol.JEFE_CONTABILIDAD), inicio)
    nucleo.registrar_actor(Actor("ADM", "Admin", rol=Rol.ADMIN), inicio)
    nucleo.registrar_entidad(EntidadContable("EMP", "Empresa"), "DIR", inicio)
    nucleo.registrar_hecho(HechoEconomico(
        hecho_id="H-AUT", entidad_id="EMP", tipo="EJECUCION_SERVICIO",
        descripcion="Hecho para intervención",
        ocurrido=FechaEconomica(TipoFecha.EXACTA, inicio=datetime(2025, 3, 31)),
        conocido_en=inicio, registrado_en=inicio, estado_economico="EJECUTADO",
    ), "DIR")

    nucleo.conceder_permiso("P-1", "DIR", "JEF", "ASIENTO_DIARIO", "EMP", datetime(2025, 4, 2))
    nucleo.revocar_permiso("P-1", "DIR", "Cambio de competencia", datetime(2025, 4, 3))
    nucleo.cambiar_modo_contabilidad(
        "EMP", ModoContabilidad.EXTRAORDINARIO_CRITICO, "DIR", datetime(2025, 4, 4), "Motivo",
    )
    nucleo.registrar_avocacion(
        "AV-1", "DIR", "JEF", "CIERRE_EJERCICIO", "EMP", datetime(2025, 4, 5), "Motivo",
    )
    nucleo.registrar_inhibicion(
        "IN-1", "JEF", "DIR", "CIERRE_EJERCICIO", "EMP", datetime(2025, 4, 6), "Motivo",
    )
    nucleo.registrar_visado(
        "VIS-1", "SUB", "REG-1", "REGISTRO_NO_ASIENTO", datetime(2025, 4, 7), "Motivo",
    )
    nucleo.solicitar_intervencion_admin("SOL-1", "JEF", "ADM", datetime(2025, 4, 8), "Motivo")
    nucleo.presentar_informe_admin(
        "INF-1", "SOL-1", "JEF", datetime(2025, 4, 9), "Sustancia", "Alta",
    )
    nucleo.validar_informe_admin("INF-1", "DIR", True, datetime(2025, 4, 10), "Motivo")
    nucleo.registrar_remision_investigacion(
        "REM-1", "H-AUT", "JEF", datetime(2025, 4, 11), "Motivo",
    )
    nucleo.finalizar_remision_investigacion("REM-1", "INF-1", datetime(2025, 4, 12), "Motivo")
    nucleo.registrar_registro_no_asiento(
        "RNA-1", "CONFIG", "JEF", "SUB", "causa", datetime(2025, 4, 13),
    )

    anterior = nucleo.reconstruir(datetime(2025, 4, 1, 12))
    estado = nucleo.reconstruir(datetime(2025, 4, 14))

    assert anterior["permisos"] == {}
    assert anterior["registros_no_asiento"] == {}
    assert estado["permisos"]["P-1"]["revocada_en"] == "2025-04-03T00:00:00"
    assert estado["modos_entidad"]["EMP"] == ModoContabilidad.EXTRAORDINARIO_CRITICO.value
    assert estado["avocaciones"]["AV-1"]["superior"] == "DIR"
    assert estado["inhibiciones"]["IN-1"]["inferior"] == "JEF"
    assert estado["visados"]["VIS-1"]["visador"] == "SUB"
    assert estado["solicitudes_admin"]["SOL-1"]["solicitante"] == "JEF"
    assert estado["informes_admin"]["INF-1"]["validado"] is True
    assert estado["informes_admin"]["INF-1"]["validado_por"] == "DIR"
    assert estado["remisiones"]["REM-1"]["informe"] == "INF-1"
    assert estado["registros_no_asiento"]["RNA-1"]["ejecutado_por"] == "JEF"
    assert "A-1" not in nucleo.autorizaciones
