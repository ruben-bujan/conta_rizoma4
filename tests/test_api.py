# -*- coding: utf-8 -*-
"""Tests de la API HTTP."""
from datetime import date

import psycopg
import pytest
from fastapi.testclient import TestClient

from conta_rizoma4.api.main import app
from conta_rizoma4.partida_doble.persistencia import PG_URL


client = TestClient(app)

EMPRESA = "TEST_API_EMPRESA"


def _limpiar():
    with psycopg.connect(PG_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM linea_asiento WHERE empresa_id = %s", (EMPRESA,)
            )
            cur.execute(
                "DELETE FROM asiento_contable WHERE empresa_id = %s", (EMPRESA,)
            )
        conn.commit()


@pytest.fixture
def api_limpia():
    _limpiar()
    yield
    _limpiar()


class TestHealth:
    def test_health(self):
        r = client.get("/health")
        assert r.status_code == 200
        d = r.json()
        assert d["status"] == "ok"
        assert d["empresas_configuradas"] >= 1

    def test_docs(self):
        r = client.get("/docs")
        assert r.status_code == 200


class TestEmpresas:
    def test_listar(self):
        r = client.get("/empresas")
        assert r.status_code == 200
        empresas = r.json()
        assert len(empresas) >= 1
        ids = [e["empresa_id"] for e in empresas]
        assert "default" in ids

    def test_obtener(self):
        r = client.get("/empresas/default")
        assert r.status_code == 200
        assert r.json()["empresa_id"] == "default"

    def test_inexistente(self):
        r = client.get("/empresas/NO_EXISTE")
        assert r.status_code == 404


class TestAsientos:
    def test_listar_vacio(self, api_limpia):
        r = client.get(f"/asientos?empresa_id={EMPRESA}")
        assert r.status_code == 200
        assert r.json() == []

    def test_crear_asiento(self, api_limpia):
        r = client.post("/asientos", json={
            "empresa_id": EMPRESA,
            "codigo_acto": "A_FACT_EMIT_SERV_NAC_SIN_RET",
            "fecha": "2025-04-15",
            "concepto": "Test API",
            "creado_por": "test",
            "parametros": {
                "base_centimos": 100000,
                "iva_pct": 21,
                "cliente_nif": "B12345678",
            },
        })
        assert r.status_code == 201, r.text
        d = r.json()
        assert d["indice"] == 0
        assert len(d["lineas"]) == 3
        assert d["hash_previo"] == "0" * 64

    def test_obtener_asiento(self, api_limpia):
        client.post("/asientos", json={
            "empresa_id": EMPRESA,
            "codigo_acto": "A_COBRO_CLIENTE_TRANSF",
            "fecha": "2025-04-15",
            "concepto": "Cobro",
            "creado_por": "test",
            "parametros": {
                "importe_centimos": 121000,
                "cliente_nif": "B12345678",
            },
        })
        r = client.get(f"/asientos/0?empresa_id={EMPRESA}")
        assert r.status_code == 200
        assert r.json()["concepto"] == "Cobro"

    def test_crear_codigo_invalido(self, api_limpia):
        r = client.post("/asientos", json={
            "empresa_id": EMPRESA,
            "codigo_acto": "A_NO_EXISTE",
            "fecha": "2025-04-15",
            "concepto": "X",
            "creado_por": "test",
            "parametros": {},
        })
        assert r.status_code == 400
        assert "Acto desconocido" in r.json()["detail"]


class TestVerificar:
    def test_verificar_vacio(self, api_limpia):
        r = client.post("/verificar", json={"empresa_id": EMPRESA})
        assert r.status_code == 200
        d = r.json()
        assert d["total"] == 0
        assert d["cadena_valida"] is True

    def test_verificar_con_asiento(self, api_limpia):
        client.post("/asientos", json={
            "empresa_id": EMPRESA,
            "codigo_acto": "A_COBRO_CLIENTE_TRANSF",
            "fecha": "2025-04-15",
            "concepto": "Cobro",
            "creado_por": "test",
            "parametros": {
                "importe_centimos": 121000,
                "cliente_nif": "B12345678",
            },
        })
        r = client.post("/verificar", json={"empresa_id": EMPRESA})
        assert r.status_code == 200
        d = r.json()
        assert d["total"] == 1
        assert d["cadena_valida"] is True
