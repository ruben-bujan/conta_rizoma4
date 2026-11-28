"""Pruebas de diario, mayor y balance de comprobación en memoria."""
from datetime import datetime


def _representaciones():
    from conta_rizoma4.dominio import Linea, RepresentacionContable

    factura = RepresentacionContable(
        "R-FACTURA", ("H-1",), "I-1", "D-1", ("C-1",), "PGC_ES",
        datetime(2025, 4, 12),
        (Linea("430", debe=121000), Linea("705", haber=100000), Linea("477", haber=21000)),
        autorizacion_id="A-1",
    )
    cobro = RepresentacionContable(
        "R-COBRO", ("H-2",), "I-2", "D-2", ("C-1",), "PGC_ES",
        datetime(2025, 4, 18),
        (Linea("572", debe=50000), Linea("430", haber=50000)),
        autorizacion_id="A-2",
    )
    return [factura, cobro]


def test_diario_ordenado_por_fecha():
    from conta_rizoma4.dominio.servicios.libros import diario

    resultado = diario(reversed(_representaciones()))

    assert resultado[0].representacion_id == "R-FACTURA"


def test_mayor_separa_cuenta_430():
    from conta_rizoma4.dominio.servicios.libros import mayor

    resultado = mayor(_representaciones())

    assert resultado["430"]["debe"] == 121000
    assert resultado["430"]["haber"] == 50000
    assert resultado["430"]["saldo"] == 71000


def test_balance_cuadra():
    from conta_rizoma4.dominio.servicios.libros import balance_comprobacion

    resultado = balance_comprobacion(_representaciones())

    assert resultado["cuadra"]
