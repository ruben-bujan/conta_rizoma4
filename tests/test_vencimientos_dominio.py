"""Pruebas de vencimientos y antigüedad de deuda."""
from datetime import datetime


def test_vencimiento_no_vencido():
    from conta_rizoma4.dominio import Vencimiento
    from conta_rizoma4.dominio.servicios.vencimientos import antiguedad_vencimiento

    vencimiento = Vencimiento(
        vencimiento_id="V-1",
        movimiento_id="M-1",
        entidad_id="EMP-A",
        tercero_id="T-1",
        tipo="COBRO",
        importe=50000,
        fecha_vencimiento=datetime(2025, 5, 1),
    )

    assert antiguedad_vencimiento(vencimiento, datetime(2025, 4, 18)) == "NO_VENCIDO"


def test_vencimiento_mas_90_dias():
    from conta_rizoma4.dominio import Vencimiento
    from conta_rizoma4.dominio.servicios.vencimientos import antiguedad_vencimiento

    vencimiento = Vencimiento(
        vencimiento_id="V-2",
        movimiento_id="M-2",
        entidad_id="EMP-A",
        tercero_id="T-1",
        tipo="COBRO",
        importe=50000,
        fecha_vencimiento=datetime(2025, 1, 1),
    )

    assert antiguedad_vencimiento(vencimiento, datetime(2025, 4, 18)) == "MAS_90_DIAS"
