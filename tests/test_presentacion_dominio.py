"""Pruebas de presentación normativa derivada."""


def test_presentacion_pgc_separa_balance_y_pyg():
    from conta_rizoma4.dominio.presentacion.presentacion import presentar_pgc

    mayor = {
        "430": {"saldo": 71000},
        "705": {"saldo": -100000},
        "600": {"saldo": 50000},
        "572": {"saldo": 50000},
    }

    presentacion = presentar_pgc(mayor)

    assert "430" in presentacion.balance_situacion["activo"]
    assert "705" in presentacion.cuenta_pyg["ingresos"]
    assert "600" in presentacion.cuenta_pyg["gastos"]


def test_presentacion_303_contiene_resultado():
    from conta_rizoma4.dominio.fiscal.modelos import Modelo303
    from conta_rizoma4.dominio.presentacion.presentacion import presentar_303

    presentacion = presentar_303(
        Modelo303(iva_repercutido=21000, iva_soportado=10500),
        periodo="2025-T1",
    )

    assert presentacion.modelo == "303"
    assert presentacion.datos["resultado"] == "A_INGRESAR"


def test_presentacion_pgc_separa_patrimonio_neto_y_pasivo_y_cuadra():
    from conta_rizoma4.dominio.presentacion.presentacion import presentar_pgc

    mayor = {
        "100": {"saldo": -100_000},
        "170": {"saldo": -40_000},
        "572": {"saldo": 160_000},
        "281": {"saldo": -10_000},
        "600": {"saldo": 20_000},
        "705": {"saldo": -30_000},
    }
    salida = presentar_pgc(mayor)

    assert salida.balance_situacion["patrimonio_neto"]["100"] == 100_000
    assert salida.balance_situacion["pasivo"]["170"] == 40_000
    assert salida.balance_situacion["activo"]["281"] == -10_000
    assert salida.cuenta_pyg["resultado"] == 10_000
    assert salida.cuadre is True


def test_presentacion_pgc_no_oculta_cuentas_sin_regla():
    from conta_rizoma4.dominio.presentacion.presentacion import presentar_pgc

    salida = presentar_pgc({"999": {"saldo": 123}})
    assert salida.cuentas_sin_clasificar == {"999": 123}
    assert salida.balance_situacion["cuadra"] is None


def test_presentacion_pgc_permite_excepciones_por_prefijo_mas_especifico():
    from conta_rizoma4.dominio.presentacion.presentacion import presentar_pgc

    salida = presentar_pgc({"407": {"saldo": 20}, "438": {"saldo": -20}})
    assert salida.balance_situacion["activo"]["407"] == 20
    assert salida.balance_situacion["pasivo"]["438"] == 20
    assert salida.cuadre is True
