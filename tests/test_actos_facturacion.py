# -*- coding: utf-8 -*-
"""Golden tests de los 14 actos de facturación.

Cada test verifica:
  - El asiento cuadra (debe = haber).
  - Las líneas son las esperadas (cuenta + debe/haber).
"""
from datetime import date

import pytest

from conta_rizoma4.actos.facturacion import (
    ACTOS, crear_acto,
    fact_emit_serv_nac_con_ret, fact_emit_serv_nac_sin_ret,
    fact_emit_serv_intra, fact_emit_serv_export,
    fact_emit_merc_nac, fact_rect_emit,
    fact_rec_gasto_nac, fact_rec_gasto_profesional,
    fact_rec_inmov, fact_rect_rec,
    cobro_cliente_transf, pago_proveedor_transf, anticipo_cliente,
    nomina_mensual,
)


GENESIS = "0" * 64
FECHA = date(2025, 4, 15)


def _lineas_a_dict(acto):
    return [
        {"cuenta": l.cuenta_pgc, "debe": l.debe_centimos, "haber": l.haber_centimos}
        for l in acto.lineas
    ]


class TestServiciosNacional:
    def test_con_retencion_1000_21_15(self):
        a = fact_emit_serv_nac_con_ret(
            indice=0, hash_previo=GENESIS, fecha=FECHA,
            base_centimos=100_000, iva_pct=21, retencion_pct=15,
            cliente_nif="B12345678", concepto="Servicios abril",
        )
        # 430 D=106000, 705 H=100000, 477 H=21000, 473 D=15000
        assert a.cuadra
        assert a.total_debe == 121_000
        assert a.total_haber == 121_000
        d = _lineas_a_dict(a)
        assert {"cuenta": "430", "debe": 106_000, "haber": 0} in d
        assert {"cuenta": "705", "debe": 0, "haber": 100_000} in d
        assert {"cuenta": "477", "debe": 0, "haber": 21_000} in d
        assert {"cuenta": "473", "debe": 15_000, "haber": 0} in d

    def test_sin_retencion_1000_21(self):
        a = fact_emit_serv_nac_sin_ret(
            indice=1, hash_previo=GENESIS, fecha=FECHA,
            base_centimos=100_000, iva_pct=21,
            cliente_nif="B12345678", concepto="Servicios",
        )
        assert a.cuadra
        assert a.total_debe == 121_000
        d = _lineas_a_dict(a)
        assert {"cuenta": "430", "debe": 121_000, "haber": 0} in d
        assert {"cuenta": "705", "debe": 0, "haber": 100_000} in d
        assert {"cuenta": "477", "debe": 0, "haber": 21_000} in d


class TestServiciosInternacional:
    def test_intracomunitaria(self):
        a = fact_emit_serv_intra(
            indice=2, hash_previo=GENESIS, fecha=FECHA,
            base_centimos=100_000, cliente_nif="DE123456789",
            concepto="Servicios a cliente UE",
        )
        assert a.cuadra
        assert a.total_debe == 100_000
        d = _lineas_a_dict(a)
        assert {"cuenta": "430", "debe": 100_000, "haber": 0} in d
        assert {"cuenta": "705", "debe": 0, "haber": 100_000} in d

    def test_exportacion(self):
        a = fact_emit_serv_export(
            indice=3, hash_previo=GENESIS, fecha=FECHA,
            base_centimos=100_000, cliente_nif="US123456789",
            concepto="Servicios a cliente USA",
        )
        assert a.cuadra
        assert a.total_debe == 100_000


class TestMercaderiasNacional:
    def test_venta_merc_1000_21(self):
        a = fact_emit_merc_nac(
            indice=4, hash_previo=GENESIS, fecha=FECHA,
            base_centimos=100_000, iva_pct=21,
            cliente_nif="B12345678", concepto="Venta mercaderías",
        )
        assert a.cuadra
        assert a.total_debe == 121_000
        d = _lineas_a_dict(a)
        assert {"cuenta": "700", "debe": 0, "haber": 100_000} in d
        assert {"cuenta": "477", "debe": 0, "haber": 21_000} in d


class TestFacturaRectificativa:
    def test_abono_emitido_500_21(self):
        a = fact_rect_emit(
            indice=5, hash_previo=GENESIS, fecha=FECHA,
            base_centimos=50_000, iva_pct=21,
            cliente_nif="B12345678", concepto="Abono",
        )
        assert a.cuadra
        # 708 D=50000, 477 D=10500, 430 H=60500
        assert a.total_debe == 60_500
        assert a.total_haber == 60_500
        d = _lineas_a_dict(a)
        assert {"cuenta": "708", "debe": 50_000, "haber": 0} in d
        assert {"cuenta": "477", "debe": 10_500, "haber": 0} in d
        assert {"cuenta": "430", "debe": 0, "haber": 60_500} in d


class TestGastoNacional:
    def test_gasto_suministros_500_21(self):
        a = fact_rec_gasto_nac(
            indice=6, hash_previo=GENESIS, fecha=FECHA,
            base_centimos=50_000, iva_pct=21,
            cuenta_gasto="628", proveedor_nif="B87654321",
            concepto="Factura luz",
        )
        assert a.cuadra
        assert a.total_debe == 60_500
        d = _lineas_a_dict(a)
        assert {"cuenta": "628", "debe": 50_000, "haber": 0} in d
        assert {"cuenta": "472", "debe": 10_500, "haber": 0} in d
        assert {"cuenta": "400", "debe": 0, "haber": 60_500} in d

    def test_gasto_profesional_1000_21_15(self):
        a = fact_rec_gasto_profesional(
            indice=7, hash_previo=GENESIS, fecha=FECHA,
            base_centimos=100_000, iva_pct=21, retencion_pct=15,
            cuenta_gasto="623", proveedor_nif="12345678Z",
            concepto="Honorarios abogado",
        )
        assert a.cuadra
        # D: 623 100000, 472 21000. H: 4751 15000, 410 106000
        assert a.total_debe == 121_000
        assert a.total_haber == 121_000
        d = _lineas_a_dict(a)
        assert {"cuenta": "623", "debe": 100_000, "haber": 0} in d
        assert {"cuenta": "472", "debe": 21_000, "haber": 0} in d
        assert {"cuenta": "4751", "debe": 0, "haber": 15_000} in d
        assert {"cuenta": "410", "debe": 0, "haber": 106_000} in d


class TestInmovilizado:
    def test_compra_ordenador_1200_21(self):
        a = fact_rec_inmov(
            indice=8, hash_previo=GENESIS, fecha=FECHA,
            base_centimos=120_000, iva_pct=21,
            cuenta_inmov="217", proveedor_nif="B11111111",
            concepto="Compra ordenador",
        )
        assert a.cuadra
        assert a.total_debe == 145_200
        d = _lineas_a_dict(a)
        assert {"cuenta": "217", "debe": 120_000, "haber": 0} in d
        assert {"cuenta": "472", "debe": 25_200, "haber": 0} in d


class TestAbonoProveedor:
    def test_abono_recibido_200_21(self):
        a = fact_rect_rec(
            indice=9, hash_previo=GENESIS, fecha=FECHA,
            base_centimos=20_000, iva_pct=21,
            cuenta_gasto="628", proveedor_nif="B87654321",
            concepto="Abono proveedor",
        )
        assert a.cuadra
        assert a.total_debe == 24_200


class TestCobroPago:
    def test_cobro_cliente(self):
        a = cobro_cliente_transf(
            indice=10, hash_previo=GENESIS, fecha=FECHA,
            importe_centimos=121_000, cliente_nif="B12345678",
            concepto="Cobro factura",
        )
        assert a.cuadra
        d = _lineas_a_dict(a)
        assert {"cuenta": "572", "debe": 121_000, "haber": 0} in d
        assert {"cuenta": "430", "debe": 0, "haber": 121_000} in d

    def test_pago_proveedor(self):
        a = pago_proveedor_transf(
            indice=11, hash_previo=GENESIS, fecha=FECHA,
            importe_centimos=60_500, proveedor_nif="B87654321",
            concepto="Pago factura",
        )
        assert a.cuadra
        assert a.total_debe == 60_500

    def test_anticipo_cliente(self):
        a = anticipo_cliente(
            indice=12, hash_previo=GENESIS, fecha=FECHA,
            importe_centimos=50_000, cliente_nif="B12345678",
            concepto="Anticipo",
        )
        assert a.cuadra
        d = _lineas_a_dict(a)
        assert {"cuenta": "438", "debe": 0, "haber": 50_000} in d


class TestNomina:
    def test_nomina_2000_15_6_30(self):
        a = nomina_mensual(
            indice=13, hash_previo=GENESIS, fecha=FECHA,
            bruto_centimos=200_000, irpf_pct=15,
            ss_trabajador_pct=6.35, ss_empresa_pct=30,
            trabajador_nif="12345678Z", concepto="Nómina abril",
        )
        assert a.cuadra
        # bruto=200000, irpf=30000, ss_trab=12700, ss_emp=60000
        # neto = 200000 - 30000 - 12700 = 157300
        # ss_total = 12700 + 60000 = 72700
        # D: 640 200000 + 642 60000 = 260000
        # H: 4751 30000 + 476 72700 + 572 157300 = 260000
        assert a.total_debe == 260_000
        assert a.total_haber == 260_000
        d = _lineas_a_dict(a)
        assert {"cuenta": "640", "debe": 200_000, "haber": 0} in d
        assert {"cuenta": "642", "debe": 60_000, "haber": 0} in d
        assert {"cuenta": "4751", "debe": 0, "haber": 30_000} in d
        assert {"cuenta": "476", "debe": 0, "haber": 72_700} in d
        assert {"cuenta": "572", "debe": 0, "haber": 157_300} in d


class TestDispatcher:
    def test_crear_acto_con_codigo(self):
        a = crear_acto(
            "A_COBRO_CLIENTE_TRANSF",
            indice=20, hash_previo=GENESIS, fecha=FECHA,
            importe_centimos=100_000, cliente_nif="B12345678",
            concepto="Cobro test",
        )
        assert a.cuadra

    def test_crear_acto_codigo_invalido(self):
        with pytest.raises(ValueError, match="Acto desconocido"):
            crear_acto("A_NO_EXISTE", indice=0, hash_previo=GENESIS)

    def test_todos_los_actos_estan_en_dict(self):
        assert len(ACTOS) == 14
