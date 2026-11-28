"""Pruebas integradas del primer paquete de migración."""
from datetime import date, datetime

from .adaptadores import representacion_poc_a_asiento
from .catalogo import cargar_catalogo
from .migracion import listar_primer_paquete
from .modelo import Linea
from .nucleo import NucleoEpistemicoContable


def test_paquete_migracion_no_superpone_catalogo_legacy():
    catalogo = {item.codigo for item in cargar_catalogo()}
    paquete = {item.codigo for item in listar_primer_paquete()}
    assert paquete
    assert paquete.issubset(catalogo)


def test_factura_y_cobro_se_representan_en_memoria():
    nucleo = NucleoEpistemicoContable()

    factura = representacion_poc_a_asiento(
        indice=1,
        fecha=date(2025, 4, 12),
        concepto="Factura emitida",
        lineas_poc=(Linea("430", debe=121000), Linea("705", haber=121000)),
        hash_previo="0" * 64,
    )
    cobro = representacion_poc_a_asiento(
        indice=2,
        fecha=date(2025, 4, 18),
        concepto="Cobro parcial",
        lineas_poc=(Linea("572", debe=50000), Linea("430", haber=50000)),
        hash_previo=factura.hash,
    )

    assert factura.cuadra
    assert cobro.cuadra
    assert cobro.hash_previo == factura.hash


def test_reconstruccion_y_catalogo_pueden_coexistir():
    nucleo = NucleoEpistemicoContable()
    catalogo = cargar_catalogo()

    assert len(catalogo) == 115
    assert nucleo.verificar_cadena()["cadena_valida"]
    assert nucleo.reconstruir(datetime(2025, 4, 18))["eventos_disponibles"] == 0
