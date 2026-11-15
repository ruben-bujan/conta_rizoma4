# -*- coding: utf-8 -*-
"""Tests del contrato economico/contabilidad.

Verifica:
  - El contrato se registra en el registro de rizoma4.
  - Las 905 cuentas válidas del PGC se cargan de Postgres.
  - Los 6 niveles de actividad se cargan de Postgres.
  - Los 23 tipos de documento (C) están completos.
  - Los interlocutores (B) son dataclasses puras.
"""
from __future__ import annotations

import pytest

from conta_rizoma4.contratos import (
    CONTRATO_ECONOMICO_CONTABILIDAD,
    CuentaPGC,
    TipoDocumento,
    TIPOS_DOCUMENTO,
    TipoPersona,
    cargar_cuentas_pgc,
    cargar_todas_las_cuentas_pgc,
    cargar_jerarquia_actividad,
    contrato_economico_contabilidad,
    invalidar_cache_actividad,
    invalidar_cache_cuentas,
    registrar_contratos,
)


class TestContrato:
    def test_contrato_tiene_dominio_y_subdominio(self):
        c = contrato_economico_contabilidad()
        assert c.dominio == "economico"
        assert c.subdominio == "contabilidad"

    def test_contrato_esta_registrado(self):
        reg = registrar_contratos()
        c = reg.obtener("economico", "contabilidad")
        assert c is not None
        assert c.dominio == "economico"

    def test_contrato_tiene_hipotesis_de_clasificacion(self):
        c = contrato_economico_contabilidad()
        ids = [h[0] for h in c.hipotesis]
        assert "H_CLASIFICACION_CORRECTA" in ids

    def test_reglas_incluyen_905_cuentas(self):
        c = contrato_economico_contabilidad()
        assert c.reglas["cuentas_pgc_total"] == 905


class TestCuentasPGC:
    def test_carga_905_cuentas_unicas(self):
        invalidar_cache_cuentas()
        cuentas = cargar_cuentas_pgc()
        assert len(cuentas) == 905, f"Esperadas 905, hay {len(cuentas)}"

    def test_carga_todas_las_cuentas_validas(self):
        filas = cargar_todas_las_cuentas_pgc()
        assert len(filas) == 905, f"Esperadas 905, hay {len(filas)}"

    def test_cuenta_capital(self):
        cuentas = cargar_cuentas_pgc()
        assert "10" in cuentas
        assert "CAPITAL" in cuentas["10"].descripcion.upper()

    def test_cuenta_banco(self):
        cuentas = cargar_cuentas_pgc()
        bancos = [c for c in cuentas.values() if c.cuenta.startswith("572")]
        assert bancos, "No hay cuentas 572 (bancos)"

    def test_niveles_de_cuenta(self):
        cuentas = cargar_cuentas_pgc()
        niveles = {c.nivel for c in cuentas.values()}
        assert 2 in niveles
        assert 5 in niveles


class TestActividad:
    def test_carga_6_niveles(self):
        invalidar_cache_actividad()
        jer = cargar_jerarquia_actividad()
        assert set(jer.keys()) == {
            "nivel1", "nivel2", "nivel3", "nivel4", "nivel5", "nivel6",
        }

    def test_nivel1_tiene_77(self):
        jer = cargar_jerarquia_actividad()
        assert len(jer["nivel1"]) == 77

    def test_nivel2_tiene_416(self):
        jer = cargar_jerarquia_actividad()
        assert len(jer["nivel2"]) == 416

    def test_nivel6_tiene_11(self):
        jer = cargar_jerarquia_actividad()
        assert len(jer["nivel6"]) == 11


class TestDocumento:
    def test_tipos_documento_completos(self):
        assert len(TIPOS_DOCUMENTO) == 23
        assert "FACTURA_EMITIDA" in TIPOS_DOCUMENTO
        assert "FACTURA_RECIBIDA" in TIPOS_DOCUMENTO
        assert "NOMINA" in TIPOS_DOCUMENTO
        assert "EXTRACTO_BANCARIO" in TIPOS_DOCUMENTO
        assert "BUROFAX" in TIPOS_DOCUMENTO
        assert "REQUERIMIENTO" in TIPOS_DOCUMENTO

    def test_tipo_documento_enum(self):
        assert TipoDocumento.FACTURA_EMITIDA.value == "FACTURA_EMITIDA"
