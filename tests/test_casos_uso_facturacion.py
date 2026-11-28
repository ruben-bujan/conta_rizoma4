"""Pruebas de casos de uso de facturación sin infraestructura."""
from datetime import datetime


def _ejercicio():
    from conta_rizoma4.dominio import EjercicioContable

    return EjercicioContable(
        ejercicio_id="E-2025",
        entidad_id="EMP-A",
        inicio=datetime(2025, 1, 1),
        fin=datetime(2025, 12, 31),
    )


def test_factura_emitida_crea_movimiento_y_asiento():
    from conta_rizoma4.dominio import Tercero
    from conta_rizoma4.dominio.casos_uso.facturacion import crear_factura_emitida

    tercero = Tercero("T-CLIENTE", "JURIDICA", "Cliente")
    resultado = crear_factura_emitida(
        entidad_id="EMP-A",
        tercero=tercero,
        ejercicio=_ejercicio(),
        hecho_ids=("H-FACTURA",),
        interpretacion_id="I-1",
        decision_id="D-1",
        criterio_ids=("C-1",),
        autorizacion_id="A-1",
        representacion_id="R-FACTURA",
        fecha=datetime(2025, 4, 12),
        base_centimos=100000,
        iva_pct=21,
        numero_factura="F-001",
    )

    assert resultado.movimiento.importe == 121000
    assert resultado.representacion.cuadra()
    assert resultado.representacion.marco == "PGC_PYMES"


def test_factura_recibida_crea_movimiento_y_asiento():
    from conta_rizoma4.dominio import Tercero
    from conta_rizoma4.dominio.casos_uso.facturacion import crear_factura_recibida

    tercero = Tercero("T-PROVEEDOR", "JURIDICA", "Proveedor")
    resultado = crear_factura_recibida(
        entidad_id="EMP-A",
        tercero=tercero,
        ejercicio=_ejercicio(),
        hecho_ids=("H-FACTURA-REC",),
        interpretacion_id="I-2",
        decision_id="D-2",
        criterio_ids=("C-1",),
        autorizacion_id="A-1",
        representacion_id="R-FACTURA-REC",
        fecha=datetime(2025, 4, 12),
        base_centimos=50000,
        iva_pct=21,
        cuenta_gasto="629",
        numero_factura="FR-001",
    )

    assert resultado.movimiento.importe == 60500
    assert resultado.representacion.cuadra()
    assert resultado.representacion.marco == "PGC_PYMES"


def test_factura_fuera_ejercicio_falla():
    from conta_rizoma4.dominio import Tercero
    from conta_rizoma4.dominio.casos_uso.facturacion import crear_factura_emitida, FacturaError

    try:
        crear_factura_emitida(
            entidad_id="EMP-A",
            tercero=Tercero("T-CLIENTE", "JURIDICA", "Cliente"),
            ejercicio=_ejercicio(),
            hecho_ids=("H-1",),
            interpretacion_id="I-1",
            decision_id="D-1",
            criterio_ids=("C-1",),
            autorizacion_id="A-1",
            representacion_id="R-1",
            fecha=datetime(2026, 1, 1),
            base_centimos=100000,
            iva_pct=21,
            numero_factura="F-X",
        )
    except FacturaError:
        return
    raise AssertionError("Debe rechazar factura fuera del ejercicio")


def test_calculo_iva_redondea_a_centimos_y_rechaza_tasa_no_finita():
    from conta_rizoma4.dominio.casos_uso.facturacion import FacturaError, calcular_iva

    assert calcular_iva(1, 50) == 1
    try:
        calcular_iva(100, float("nan"))
    except FacturaError:
        return
    raise AssertionError("Debe rechazar tipos impositivos no finitos")


def test_factura_rechaza_entidad_distinta_del_ejercicio():
    from conta_rizoma4.dominio import Tercero
    from conta_rizoma4.dominio.casos_uso.facturacion import FacturaError, crear_factura_emitida

    try:
        crear_factura_emitida(
            entidad_id="EMP-B", tercero=Tercero("T-1", "JURIDICA", "Cliente"),
            ejercicio=_ejercicio(), hecho_ids=("H-1",), interpretacion_id="I-1",
            decision_id="D-1", criterio_ids=("C-1",), autorizacion_id="A-1", representacion_id="R-1",
            fecha=datetime(2025, 4, 12), base_centimos=1000, iva_pct=21, numero_factura="F-1",
        )
    except FacturaError:
        return
    raise AssertionError("Debe rechazar entidad distinta del ejercicio")


def test_factura_ordinaria_rechaza_base_cero_y_tercero_inactivo():
    import pytest
    from conta_rizoma4.dominio import Tercero
    from conta_rizoma4.dominio.casos_uso.facturacion import FacturaError, crear_factura_emitida

    args = dict(
        entidad_id="EMP-A", tercero=Tercero("T-1", "JURIDICA", "Cliente"),
        ejercicio=_ejercicio(), hecho_ids=("H-1",), interpretacion_id="I-1",
        decision_id="D-1", criterio_ids=("C-1",), autorizacion_id="A-1", representacion_id="R-1",
        fecha=datetime(2025, 4, 12), base_centimos=0, iva_pct=21, numero_factura="F-0",
    )
    with pytest.raises(FacturaError, match="base.*positiva"):
        crear_factura_emitida(**args)

    args["base_centimos"] = 100
    args["tercero"] = Tercero("T-2", "JURIDICA", "Cliente", activo=False)
    with pytest.raises(FacturaError, match="inactivo"):
        crear_factura_emitida(**args)
