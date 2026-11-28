"""Pruebas de inmovilizado básico."""
from datetime import datetime


def _ejercicio():
    from conta_rizoma4.dominio import EjercicioContable
    return EjercicioContable(
        ejercicio_id="E-2025", entidad_id="EMP-A",
        inicio=datetime(2025, 1, 1), fin=datetime(2025, 12, 31),
    )


def test_alta_inmovilizado_cuadra():
    from conta_rizoma4.dominio.casos_uso.inmovilizado import alta_inmovilizado

    representacion = alta_inmovilizado(
        entidad_id="EMP-A", ejercicio=_ejercicio(),
        representacion_id="R-INMOV-1", interpretacion_id="I-1",
        decision_id="D-1", criterio_ids=("C-1",), hecho_ids=("H-INMOV",),
        autorizacion_id="A-1",
        fecha=datetime(2025, 4, 1), coste_centimos=120000,
        cuenta_activo="217",
    )

    assert representacion.cuadra()
    assert representacion.marco == "PGC_PYMES"


def test_amortizacion_cuadra():
    from conta_rizoma4.dominio.casos_uso.inmovilizado import amortizar_inmovilizado

    representacion = amortizar_inmovilizado(
        entidad_id="EMP-A", ejercicio=_ejercicio(),
        representacion_id="R-AMORT-1", interpretacion_id="I-1",
        decision_id="D-1", criterio_ids=("C-1",), hecho_ids=("H-AMORT",),
        autorizacion_id="A-1",
        fecha=datetime(2025, 12, 31), importe_centimos=7500,
        cuenta_gasto="681", cuenta_amortizacion="281",
    )

    assert representacion.cuadra()
    assert representacion.marco == "PGC_PYMES"


def test_cuota_lineal_reparte_centimos_y_respeta_valor_residual():
    from conta_rizoma4.dominio import calcular_cuota_amortizacion_lineal

    cuotas = [
        calcular_cuota_amortizacion_lineal(
            coste_centimos=101, valor_residual_centimos=1,
            vida_util_periodos=3, periodos_ya_amortizados=i,
        )
        for i in range(3)
    ]
    assert cuotas == [34, 33, 33]
    assert sum(cuotas) == 100
    assert calcular_cuota_amortizacion_lineal(
        coste_centimos=101, valor_residual_centimos=1,
        vida_util_periodos=3, periodos_ya_amortizados=3,
    ) == 0
