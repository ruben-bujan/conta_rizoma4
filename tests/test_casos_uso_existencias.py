"""Pruebas básicas de existencias."""
from datetime import datetime


def _ejercicio():
    from conta_rizoma4.dominio import EjercicioContable
    return EjercicioContable(
        ejercicio_id="E-2025", entidad_id="EMP-A",
        inicio=datetime(2025, 1, 1), fin=datetime(2025, 12, 31),
    )


def test_compra_existencias_cuadra():
    from conta_rizoma4.dominio.casos_uso.existencias import compra_existencias

    representacion = compra_existencias(
        entidad_id="EMP-A", ejercicio=_ejercicio(),
        representacion_id="R-COMPRA-EX", interpretacion_id="I-1",
        decision_id="D-1", criterio_ids=("C-1",), hecho_ids=("H-COMPRA",),
        autorizacion_id="A-1",
        fecha=datetime(2025, 4, 1), base_centimos=80000,
        cuenta_existencias="300",
    )

    assert representacion.cuadra()
    assert representacion.marco == "PGC_PYMES"


def test_venta_existencias_cuadra():
    from conta_rizoma4.dominio.casos_uso.existencias import venta_existencias

    representacion = venta_existencias(
        entidad_id="EMP-A", ejercicio=_ejercicio(),
        representacion_id="R-VENTA-EX", interpretacion_id="I-1",
        decision_id="D-1", criterio_ids=("C-1",), hecho_ids=("H-VENTA",),
        autorizacion_id="A-1",
        fecha=datetime(2025, 4, 2), importe_centimos=100000,
        cuenta_ingreso="700",
    )

    assert representacion.cuadra()
    assert representacion.marco == "PGC_PYMES"


def test_valoracion_fifo_y_pmp_conserva_coste_total():
    from conta_rizoma4.dominio import LoteExistencias, valorar_salida_existencias

    lotes = (LoteExistencias(2, 200), LoteExistencias(2, 400))
    fifo = valorar_salida_existencias(lotes=lotes, cantidad=1, metodo="FIFO")
    pmp = valorar_salida_existencias(lotes=lotes, cantidad=1, metodo="PMP")

    assert fifo.coste_salida_centimos == 100
    assert sum(l.coste_total_centimos for l in fifo.lotes_restantes) == 500
    assert pmp.coste_salida_centimos == 150
    assert sum(l.coste_total_centimos for l in pmp.lotes_restantes) == 450


def test_fifo_ignora_capas_anteriores_agotadas_y_rechaza_salida_excesiva():
    import pytest
    from conta_rizoma4.dominio import LoteExistencias, valorar_salida_existencias
    from conta_rizoma4.dominio.casos_uso.existencias import ExistenciasError

    salida = valorar_salida_existencias(
        lotes=(LoteExistencias(1, 90), LoteExistencias(3, 600)),
        cantidad=2, metodo="FIFO",
    )
    assert salida.coste_salida_centimos == 290
    assert salida.lotes_restantes == (LoteExistencias(2, 400),)
    with pytest.raises(ExistenciasError):
        valorar_salida_existencias(
            lotes=(LoteExistencias(1, 100),), cantidad=2, metodo="FIFO",
        )
