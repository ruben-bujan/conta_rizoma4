"""Pruebas básicas de conciliación bancaria sin banco externo."""
from datetime import datetime


def test_conciliacion_exacta():
    from conta_rizoma4.dominio import Conciliacion, CuentaBancaria, MovimientoExtracto

    cuenta = CuentaBancaria("CB-1", "EMP-A", "ES0000000000000000000000")
    extracto = MovimientoExtracto(
        movimiento_id="EX-1",
        cuenta_id=cuenta.cuenta_id,
        fecha_operacion=datetime(2025, 4, 18),
        fecha_valor=datetime(2025, 4, 18),
        importe=50000,
        descripcion="Cobro cliente",
    )
    conciliacion = Conciliacion(
        conciliacion_id="CON-1",
        movimiento_extracto_id=extracto.movimiento_id,
        movimiento_economico_id="M-COBRO",
        estado="CONCILIADO",
        diferencia=0,
    )

    assert conciliacion.estado == "CONCILIADO"
    assert conciliacion.diferencia == 0


def test_conciliacion_con_diferencia_queda_pendiente():
    from conta_rizoma4.dominio import Conciliacion

    conciliacion = Conciliacion(
        conciliacion_id="CON-2",
        movimiento_extracto_id="EX-2",
        movimiento_economico_id="M-COBRO",
        estado="DIFERENCIA",
        diferencia=-100,
        motivo="Comisión o cobro parcial",
    )

    assert conciliacion.estado == "DIFERENCIA"
    assert conciliacion.diferencia != 0


def test_conciliar_movimiento_compara_importe_firmado_sin_alterar_fuentes():
    from conta_rizoma4.dominio import (
        CuentaBancaria, MovimientoEconomico, MovimientoExtracto, conciliar_movimiento,
    )

    cuenta = CuentaBancaria("CB-1", "EMP-A", "ES0000000000000000000000")
    extracto = MovimientoExtracto("EX-1", "CB-1", datetime(2025, 4, 18), None, -5000, "Pago")
    pago = MovimientoEconomico("M-1", "EMP-A", "T-1", "PAGO", 5000, estado="PAGADO")
    conciliacion = conciliar_movimiento(
        conciliacion_id="CON-1", cuenta=cuenta, extracto=extracto, movimiento=pago,
    )

    assert conciliacion.estado == "CONCILIADO"
    assert conciliacion.diferencia == 0
    assert extracto.estado == "NO_CONCILIADO"
    assert extracto.importe == -5000


def test_diferencia_y_reporte_mantienen_pendientes_y_saldos():
    from conta_rizoma4.dominio import (
        CuentaBancaria, MovimientoEconomico, MovimientoExtracto, conciliar_movimiento,
        resumir_conciliacion,
    )

    cuenta = CuentaBancaria("CB-1", "EMP-A", "ES0000000000000000000000")
    extracto = MovimientoExtracto("EX-1", "CB-1", datetime(2025, 4, 18), None, 5100, "Cobro")
    cobro = MovimientoEconomico("M-1", "EMP-A", "T-1", "COBRO", 5000, estado="COBRADO")
    diferencia = conciliar_movimiento(
        conciliacion_id="CON-1", cuenta=cuenta, extracto=extracto, movimiento=cobro,
    )
    resumen = resumir_conciliacion(
        cuenta=cuenta, saldo_inicial_banco=1000, saldo_inicial_libros=1000,
        extractos=(extracto,), movimientos=(cobro,), conciliaciones=(diferencia,),
    )

    assert diferencia.estado == "DIFERENCIA"
    assert diferencia.diferencia == 100
    assert resumen.saldo_final_banco == 6100
    assert resumen.saldo_final_libros == 6000
    assert resumen.diferencia_saldos == 100
    assert resumen.extractos_sin_conciliar == ("EX-1",)
    assert resumen.movimientos_sin_conciliar == ("M-1",)


def test_resumen_rechaza_vinculo_conciliado_falso_o_con_referencias_ausentes():
    import pytest
    from conta_rizoma4.dominio import (
        Conciliacion, CuentaBancaria, MovimientoEconomico, MovimientoExtracto,
        ConciliacionError, resumir_conciliacion,
    )

    cuenta = CuentaBancaria("CB-1", "EMP-A", "ES0000000000000000000000")
    extracto = MovimientoExtracto("EX-1", "CB-1", datetime(2025, 4, 18), None, 5_100, "Cobro")
    cobro = MovimientoEconomico("M-1", "EMP-A", "T-1", "COBRO", 5_000, estado="COBRADO")
    falso = Conciliacion("C-1", "EX-1", "M-1", "CONCILIADO", diferencia=0)
    with pytest.raises(ConciliacionError, match="diferencia cero"):
        resumir_conciliacion(
            cuenta=cuenta, saldo_inicial_banco=0, saldo_inicial_libros=0,
            extractos=(extracto,), movimientos=(cobro,), conciliaciones=(falso,),
        )

    ausente = Conciliacion("C-2", "EX-NO-EXISTE", "M-1", "CONCILIADO")
    with pytest.raises(ConciliacionError, match="ausentes"):
        resumir_conciliacion(
            cuenta=cuenta, saldo_inicial_banco=0, saldo_inicial_libros=0,
            extractos=(extracto,), movimientos=(cobro,), conciliaciones=(ausente,),
        )


def test_no_propone_conciliar_movimiento_economico_pendiente():
    import pytest
    from conta_rizoma4.dominio import (
        CuentaBancaria, MovimientoEconomico, MovimientoExtracto,
        ConciliacionError, conciliar_movimiento,
    )

    cuenta = CuentaBancaria("CB-1", "EMP-A", "ES0000000000000000000000")
    extracto = MovimientoExtracto("EX-1", "CB-1", datetime(2025, 4, 18), None, 5000, "Cobro")
    pendiente = MovimientoEconomico("M-1", "EMP-A", "T-1", "COBRO", 5000)
    with pytest.raises(ConciliacionError, match="todavía no está cobrado"):
        conciliar_movimiento(
            conciliacion_id="C-1", cuenta=cuenta, extracto=extracto, movimiento=pendiente,
        )
