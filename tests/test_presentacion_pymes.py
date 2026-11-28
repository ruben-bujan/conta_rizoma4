from conta_rizoma4.dominio.presentacion.pymes import presentar_pymes


MAYOR = {
    "100": {"saldo": -100_000},
    "170": {"saldo": -40_000},
    "572": {"saldo": 160_000},
    "281": {"saldo": -10_000},
    "600": {"saldo": 20_000},
    "705": {"saldo": -30_000},
}


def test_paquete_pymes_exige_comparativo_memoria_y_revision():
    salida = presentar_pymes(
        MAYOR, empresa_id="E1", ejercicio="2025",
        mayor_comparativo=MAYOR, ejercicio_comparativo="2024",
        datos_memoria={"actividad": "Construcción"},
    )
    assert salida.balance["cuadra"] is True
    assert salida.cuenta_pyg["resultado"] == 10_000
    assert salida.balance_comparativo["total_activo"] == 150_000
    assert salida.pyg_comparativa["resultado"] == 10_000
    assert salida.documentos_integrantes == ("balance", "cuenta_pyg", "ecpn", "memoria")
    assert not salida.apta_para_deposito
    assert any("memoria" in pendiente.lower() for pendiente in salida.pendientes)


def test_paquete_pymes_preserva_memoria_y_senala_datos_ausentes():
    memoria = {"actividad": "Construcción"}
    salida = presentar_pymes(MAYOR, empresa_id="E1", ejercicio="2025", datos_memoria=memoria)
    memoria["actividad"] = "modificada fuera"
    assert salida.datos_memoria == {"actividad": "Construcción"}
    assert salida.balance_comparativo is None
    assert any("comparativo" in pendiente.lower() for pendiente in salida.pendientes)


def test_paquete_pymes_rechaza_identificacion_incompleta():
    try:
        presentar_pymes(MAYOR, empresa_id="", ejercicio="2025")
    except ValueError as exc:
        assert "empresa_id" in str(exc)
    else:
        raise AssertionError("Debe exigir empresa y ejercicio")


def test_paquete_pymes_conserva_ecpn_aportado_y_no_lo_infiere():
    ecpn = {
        "saldo_inicial_centimos": 100,
        "variaciones": [{"concepto": "resultado", "importe_centimos": 20}],
        "saldo_final_centimos": 120,
    }
    salida = presentar_pymes(MAYOR, empresa_id="E1", ejercicio="2025", datos_ecpn=ecpn)
    ecpn["variaciones"][0]["importe_centimos"] = 999
    assert salida.estado_cambios_patrimonio_neto["total_variaciones_centimos"] == 20
    assert salida.estado_cambios_patrimonio_neto["cuadra"] is True
    assert any("memoria" in p.lower() for p in salida.pendientes)
    assert not salida.apta_para_deposito


def test_ecpn_descuadrado_se_marca_y_no_se_infiere():
    salida = presentar_pymes(
        MAYOR, empresa_id="E1", ejercicio="2025",
        datos_ecpn={
            "saldo_inicial_centimos": 100,
            "variaciones": [{"concepto": "resultado", "importe_centimos": 20}],
            "saldo_final_centimos": 125,
        },
    )
    assert salida.estado_cambios_patrimonio_neto["diferencia_conciliacion_centimos"] == -5
    assert salida.estado_cambios_patrimonio_neto["cuadra"] is False
    assert any("no concilia" in pendiente for pendiente in salida.pendientes)


def test_paquete_traza_reglas_y_marca_sin_validacion_normativa():
    salida = presentar_pymes(MAYOR, empresa_id="E1", ejercicio="2025")
    regla_efectivo = next(r for r in salida.trazabilidad_reglas if r["prefijo"] == "57")
    assert regla_efectivo["cuentas_afectadas"] == ("572",)
    assert regla_efectivo["referencia_normativa"] is None
    assert any("referencia normativa" in p for p in salida.pendientes)
    assert not salida.apta_para_deposito


def test_regla_presentacion_rechaza_intervalo_de_vigencia_invertido():
    from datetime import date
    import pytest
    from conta_rizoma4.dominio.presentacion.presentacion import ReglaPresentacion

    with pytest.raises(ValueError, match="vigencia"):
        ReglaPresentacion(
            "57", "activo", "efectivo", 1,
            vigente_desde=date(2025, 1, 1), vigente_hasta=date(2024, 12, 31),
        )
