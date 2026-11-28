"""Pruebas fiscales separadas del núcleo contable."""


def test_modelo303_ingresar():
    from conta_rizoma4.dominio.fiscal.modelos import Modelo303

    modelo = Modelo303(iva_repercutido=21000, iva_soportado=10500)

    assert modelo.diferencia == 10500
    assert modelo.resultado == "A_INGRESAR"


def test_modelo303_compensar():
    from conta_rizoma4.dominio.fiscal.modelos import Modelo303

    modelo = Modelo303(iva_repercutido=21000, iva_soportado=30000)

    assert modelo.diferencia == -9000
    assert modelo.resultado == "A_DEVOLVER_O_COMPENSAR"


def test_modelo200_base_y_cuota():
    from conta_rizoma4.dominio.fiscal.modelos import Modelo200

    modelo = Modelo200(
        resultado_contable=100000,
        ajustes_positivos=10000,
        ajustes_negativos=5000,
        tipo_impositivo=25,
    )

    assert modelo.base_imponible == 105000
    assert modelo.cuota_integra == 26250


def test_modelo200_no_asume_tipo_impositivo_y_rechaza_tipos_invalidos():
    import pytest
    from conta_rizoma4.dominio.fiscal.modelos import Modelo200

    with pytest.raises(ValueError, match="tipo_impositivo"):
        Modelo200()
    with pytest.raises(ValueError, match="entre 0 y 100"):
        Modelo200(resultado_contable=100, tipo_impositivo=101)


def test_reglas_fiscales_conservan_vigencia_y_conocimiento_historico():
    from datetime import date, datetime
    from conta_rizoma4.dominio.fiscal import ReglaFiscal, RegistroFiscalMemoria

    registro = RegistroFiscalMemoria()
    inicial = ReglaFiscal(
        regla_id="IVA-GENERAL-2024", impuesto="IVA", clave="GENERAL",
        jurisdiccion="ES", version="2024.1",
        vigente_desde=date(2024, 1, 1), vigente_hasta=date(2025, 1, 1),
        registrada_en=datetime(2023, 12, 1), parametros=(("tipo_pct", "21"),),
        fuente_referencia="REF-NORMATIVA-2024",
    )
    corregida = ReglaFiscal(
        regla_id="IVA-GENERAL-2024-C1", impuesto="IVA", clave="GENERAL",
        jurisdiccion="ES", version="2024.1-correccion",
        vigente_desde=date(2024, 1, 1), vigente_hasta=date(2025, 1, 1),
        registrada_en=datetime(2024, 6, 1), parametros=(("tipo_pct", "20"),),
        fuente_referencia="REF-CORRECCION-2024", reemplaza_regla_id=inicial.regla_id,
    )
    registro.registrar(inicial)
    registro.registrar(corregida)

    antes = registro.resolver(
        impuesto="IVA", clave="GENERAL", jurisdiccion="ES",
        fecha_aplicacion=date(2024, 3, 1), conocida_en=datetime(2024, 5, 1),
    )
    despues = registro.resolver(
        impuesto="IVA", clave="GENERAL", jurisdiccion="ES",
        fecha_aplicacion=date(2024, 3, 1), conocida_en=datetime(2024, 7, 1),
    )

    assert antes.regla_id == "IVA-GENERAL-2024"
    assert despues.regla_id == "IVA-GENERAL-2024-C1"
    assert len(registro.reglas) == 2


def test_aplicacion_fiscal_fija_regla_y_rechaza_ambiguedad():
    from datetime import date, datetime
    import pytest
    from conta_rizoma4.dominio.fiscal import (
        ErrorReglaFiscal, ReglaFiscal, RegistroFiscalMemoria, documentar_aplicacion,
    )

    registro = RegistroFiscalMemoria()
    registro.registrar(ReglaFiscal(
        regla_id="IS-2025", impuesto="IS", clave="GENERAL", jurisdiccion="ES",
        version="2025.1", vigente_desde=date(2025, 1, 1),
        registrada_en=datetime(2025, 1, 1), parametros=(("tipo_pct", "25"),),
        fuente_referencia="REF-PENDIENTE",
    ))
    aplicacion = documentar_aplicacion(
        registro, impuesto="IS", clave="GENERAL", jurisdiccion="ES",
        fecha_aplicacion=date(2025, 4, 1), conocida_en=datetime(2025, 4, 1),
    )
    assert aplicacion.regla_id == "IS-2025"
    assert aplicacion.parametros_aplicados == (("tipo_pct", "25"),)
    with pytest.raises(ErrorReglaFiscal):
        registro.resolver(
            impuesto="IVA", clave="GENERAL", jurisdiccion="ES",
            fecha_aplicacion=date(2025, 4, 1), conocida_en=datetime(2025, 4, 1),
        )


def test_modelo_200_usa_y_traza_el_tipo_de_regla_conocido():
    from datetime import date, datetime
    from conta_rizoma4.dominio.fiscal import (
        ReglaFiscal, RegistroFiscalMemoria, calcular_modelo_200_versionado,
    )

    registro = RegistroFiscalMemoria()
    registro.registrar(ReglaFiscal(
        regla_id="IS-TEST-1", impuesto="IS", clave="GENERAL", jurisdiccion="ES",
        version="TEST-1", vigente_desde=date(2025, 1, 1),
        registrada_en=datetime(2024, 12, 1), parametros=(("tipo_pct", "25"),),
        fuente_referencia="FUENTE-TEST",
    ))
    resultado = calcular_modelo_200_versionado(
        registro, clave="GENERAL", jurisdiccion="ES",
        fecha_aplicacion=date(2025, 12, 31), conocida_en=datetime(2025, 1, 1),
        resultado_contable=10,
    )
    assert resultado.aplicacion_regla.regla_id == "IS-TEST-1"
    assert resultado.calculo.cuota_integra == 3  # 2,5 céntimos, redondeo HALF_UP


def test_calculo_de_iva_toma_porcentaje_de_regla_conocida_en_fecha():
    from datetime import date, datetime
    from conta_rizoma4.dominio.fiscal import (
        ReglaFiscal, RegistroFiscalMemoria, calcular_importe_con_regla,
    )

    registro = RegistroFiscalMemoria()
    inicial = ReglaFiscal(
        regla_id="IVA-1", impuesto="IVA", clave="GENERAL", jurisdiccion="ES",
        version="1", vigente_desde=date(2025, 1, 1), vigente_hasta=date(2026, 1, 1),
        registrada_en=datetime(2024, 12, 1), parametros=(("tipo_pct", "21"),),
        fuente_referencia="FUENTE-IVA",
    )
    corregida = ReglaFiscal(
        regla_id="IVA-2", impuesto="IVA", clave="GENERAL", jurisdiccion="ES",
        version="2", vigente_desde=date(2025, 1, 1), vigente_hasta=date(2026, 1, 1),
        registrada_en=datetime(2025, 6, 1), parametros=(("tipo_pct", "20"),),
        fuente_referencia="FUENTE-CORRECCION", reemplaza_regla_id="IVA-1",
    )
    registro.registrar(inicial)
    registro.registrar(corregida)
    antes = calcular_importe_con_regla(
        registro, impuesto="IVA", clave="GENERAL", jurisdiccion="ES",
        fecha_aplicacion=date(2025, 3, 1), conocida_en=datetime(2025, 5, 1),
        base_centimos=100,
    )
    despues = calcular_importe_con_regla(
        registro, impuesto="IVA", clave="GENERAL", jurisdiccion="ES",
        fecha_aplicacion=date(2025, 3, 1), conocida_en=datetime(2025, 7, 1),
        base_centimos=100,
    )
    assert (antes.importe_centimos, antes.aplicacion_regla.regla_id) == (21, "IVA-1")
    assert (despues.importe_centimos, despues.aplicacion_regla.regla_id) == (20, "IVA-2")


def test_modelo_303_analitico_conserva_las_dos_reglas_iva_aplicadas():
    from datetime import date, datetime
    from conta_rizoma4.dominio.fiscal import (
        ReglaFiscal, RegistroFiscalMemoria, calcular_modelo_303_versionado,
    )

    registro = RegistroFiscalMemoria()
    for regla_id, clave, tipo in (
        ("IVA-V-21", "VENTAS", "21"), ("IVA-C-10", "COMPRAS", "10"),
    ):
        registro.registrar(ReglaFiscal(
            regla_id=regla_id, impuesto="IVA", clave=clave, jurisdiccion="ES",
            version="1", vigente_desde=date(2025, 1, 1),
            registrada_en=datetime(2024, 12, 1), parametros=(("tipo_pct", tipo),),
            fuente_referencia="FUENTE-TEST",
        ))
    resultado = calcular_modelo_303_versionado(
        registro, jurisdiccion="ES", fecha_aplicacion=date(2025, 4, 1),
        conocida_en=datetime(2025, 4, 1), clave_repercutido="VENTAS",
        clave_soportado="COMPRAS", base_repercutida_centimos=10_000,
        base_soportada_centimos=5_000,
    )
    assert resultado.calculo.iva_repercutido == 2_100
    assert resultado.calculo.iva_soportado == 500
    assert [r.regla_id for r in resultado.aplicaciones_regla] == ["IVA-V-21", "IVA-C-10"]


def test_regla_fiscal_no_admite_parametros_mutables_ni_ramas_de_correccion():
    from datetime import date, datetime
    import pytest
    from conta_rizoma4.dominio.fiscal import ErrorReglaFiscal, ReglaFiscal, RegistroFiscalMemoria

    with pytest.raises(ErrorReglaFiscal, match="pares inmutables"):
        ReglaFiscal(
            regla_id="R-MUT", impuesto="IVA", clave="GENERAL", jurisdiccion="ES",
            version="1", vigente_desde=date(2025, 1, 1),
            registrada_en=datetime(2025, 1, 1), parametros=[("tipo_pct", "21")],
            fuente_referencia="FUENTE",
        )

    registro = RegistroFiscalMemoria()
    base = ReglaFiscal(
        regla_id="R1", impuesto="IVA", clave="GENERAL", jurisdiccion="ES",
        version="1", vigente_desde=date(2025, 1, 1), registrada_en=datetime(2025, 1, 1),
        parametros=(("tipo_pct", "21"),), fuente_referencia="FUENTE",
    )
    r2 = ReglaFiscal(
        regla_id="R2", impuesto="IVA", clave="GENERAL", jurisdiccion="ES",
        version="2", vigente_desde=date(2025, 1, 1), registrada_en=datetime(2025, 2, 1),
        parametros=(("tipo_pct", "20"),), fuente_referencia="CORRECCION",
        reemplaza_regla_id="R1",
    )
    rama = ReglaFiscal(
        regla_id="R3", impuesto="IVA", clave="GENERAL", jurisdiccion="ES",
        version="3", vigente_desde=date(2025, 1, 1), registrada_en=datetime(2025, 3, 1),
        parametros=(("tipo_pct", "19"),), fuente_referencia="CORRECCION-2",
        reemplaza_regla_id="R1",
    )
    registro.registrar(base)
    registro.registrar(r2)
    with pytest.raises(ErrorReglaFiscal, match="ya tiene una corrección"):
        registro.registrar(rama)
