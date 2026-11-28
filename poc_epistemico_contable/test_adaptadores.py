"""Pruebas de compatibilidad entre la POC y el código contable existente."""
from datetime import date

from .adaptadores import (
    adaptar_acto_puro,
    asiento_actual_a_lineas_poc,
    representacion_poc_a_asiento,
)
from .modelo import Linea

GENESIS = "0" * 64


def test_convertir_representacion_a_asiento_existente():
    asiento = representacion_poc_a_asiento(
        indice=100,
        fecha=date(2025, 4, 12),
        concepto="Servicio prestado",
        lineas_poc=(Linea("430", debe=121000), Linea("705", haber=121000)),
        hash_previo=GENESIS,
    )
    assert asiento.cuadra
    assert asiento.total_debe == 121000
    assert asiento.total_haber == 121000


def test_convertir_lineas_hacia_poc():
    asiento = representacion_poc_a_asiento(
        indice=101,
        fecha=date(2025, 4, 12),
        concepto="Cliente",
        lineas_poc=(Linea("430", debe=121000), Linea("705", haber=121000)),
        hash_previo=GENESIS,
    )
    lineas = asiento_actual_a_lineas_poc(asiento)
    assert lineas[0].cuenta == "430"
    assert lineas[0].debe == 121000


def test_ejecutar_acto_puro_sin_persistencia():
    def acto_puro(*, indice, hash_previo, fecha, concepto):
        return representacion_poc_a_asiento(
            indice=indice,
            fecha=fecha,
            concepto=concepto,
            lineas_poc=(Linea("430", debe=121000), Linea("705", haber=121000)),
            hash_previo=hash_previo,
        )

    asiento = adaptar_acto_puro(
        acto_puro,
        indice=102,
        hash_previo=GENESIS,
        fecha=date(2025, 4, 12),
        concepto="Factura POC",
    )
    assert asiento.cuadra
