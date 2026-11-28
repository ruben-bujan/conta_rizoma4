"""Pruebas de terceros y movimientos económicos asociados."""


def test_tercero_identificador_fiscal_no_verificado_por_defecto():
    from conta_rizoma4.dominio import Tercero

    tercero = Tercero(
        tercero_id="T-1",
        tipo="JURIDICA",
        nombre="Empresa Prueba",
        identificador_fiscal="B12345678",
    )

    assert tercero.identidad_fiscal_estado == "NO_VERIFICADA"


def test_tercero_requiere_tipo():
    from conta_rizoma4.dominio import Tercero

    try:
        Tercero("T-2", "", "Entidad sin tipo")
    except ValueError:
        return
    raise AssertionError("Un tercero requiere tipo")


def test_movimiento_abierto_por_tercero():
    from datetime import datetime
    from conta_rizoma4.dominio import MovimientoEconomico

    movimiento = MovimientoEconomico(
        movimiento_id="M-1",
        entidad_id="EMP-A",
        tercero_id="T-1",
        tipo="DERECHO_COBRO",
        importe=121000,
        fecha_documental=datetime(2025, 4, 12),
        fecha_vencimiento=datetime(2025, 5, 12),
    )

    assert movimiento.estado == "PENDIENTE"
    assert movimiento.tercero_id == "T-1"


def test_movimiento_rechaza_importe_negativo():
    from conta_rizoma4.dominio import MovimientoEconomico

    try:
        MovimientoEconomico(
            movimiento_id="M-2",
            entidad_id="EMP-A",
            tercero_id="T-1",
            tipo="COBRO",
            importe=-1,
        )
    except ValueError:
        return
    raise AssertionError("Un movimiento no puede tener importe negativo")
