# -*- coding: utf-8 -*-
"""Tests de la API HTTP."""
from datetime import date

import psycopg
import pytest
from fastapi.testclient import TestClient

from conta_rizoma4.api.main import app
from conta_rizoma4.partida_doble.persistencia import PG_URL
from conta_rizoma4.custodia.casos_rizoma4 import RepositorioCasoRizoma4
from test_helpers_auth import sembrar_usuario


client = TestClient(app)

EMPRESA = "TEST_API_EMPRESA"
EMAIL = "test_api_user@example.com"
USUARIO_ID = "TEST_API_USER_ID"
CASO_ID = "TEST_API_CASE_01"


def _limpiar():
    with psycopg.connect(PG_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM linea_asiento WHERE empresa_id = %s", (EMPRESA,)
            )
            cur.execute(
                "DELETE FROM asiento_contable WHERE empresa_id = %s", (EMPRESA,)
            )
            cur.execute("DELETE FROM empresa_casos_rizoma4 WHERE empresa_id = %s", (EMPRESA,))
            cur.execute("DELETE FROM usuarios WHERE email = %s", (EMAIL,))
        conn.commit()


@pytest.fixture(autouse=True)
def api_limpia():
    _limpiar()
    sembrar_usuario(usuario_id=USUARIO_ID, email=EMAIL,
                    password="test-password-1234", nombre="Test API User",
                    rol="admin", empresa_id=EMPRESA)
    r_login = client.post("/auth/login", json={
        "email": EMAIL,
        "password": "test-password-1234",
    })
    if r_login.status_code == 200:
        token = r_login.json()["access_token"]
        client.headers["Authorization"] = f"Bearer {token}"
    RepositorioCasoRizoma4().asociar(EMPRESA, CASO_ID, USUARIO_ID)

    yield

    client.headers.pop("Authorization", None)
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
    def test_listar_vacio(self):
        r = client.get(f"/asientos?empresa_id={EMPRESA}")
        assert r.status_code == 200
        assert r.json() == []

    def test_crear_asiento(self):
        r = client.post("/asientos", json={
            "empresa_id": EMPRESA,
            "caso_id": CASO_ID,
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
        assert d["caso_id"] == CASO_ID
        assert d["metadatos"]["caso_id"] == CASO_ID
        assert len(d["lineas"]) == 3
        assert d["hash_previo"] == "0" * 64

    def test_obtener_asiento(self):
        client.post("/asientos", json={
            "empresa_id": EMPRESA,
            "caso_id": CASO_ID,
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
        assert r.json()["caso_id"] == CASO_ID

    def test_crear_codigo_invalido(self):
        r = client.post("/asientos", json={
            "empresa_id": EMPRESA,
            "caso_id": CASO_ID,
            "codigo_acto": "A_NO_EXISTE",
            "fecha": "2025-04-15",
            "concepto": "X",
            "creado_por": "test",
            "parametros": {},
        })
        assert r.status_code == 400
        assert "Acto desconocido" in r.json()["detail"]

    def test_crear_asiento_rechaza_caso_no_asociado(self):
        r = client.post("/asientos", json={
            "empresa_id": EMPRESA,
            "caso_id": "CASO_NO_ASOCIADO",
            "codigo_acto": "A_COBRO_CLIENTE_TRANSF",
            "fecha": "2025-04-15",
            "concepto": "Caso no asociado",
            "creado_por": "test",
            "parametros": {
                "importe_centimos": 121000,
                "cliente_nif": "B12345678",
            },
        })
        assert r.status_code == 422


class TestVerificar:
    def test_verificar_vacio(self):
        r = client.post("/verificar", json={"empresa_id": EMPRESA})
        assert r.status_code == 200
        d = r.json()
        assert d["total"] == 0
        assert d["cadena_valida"] is True

    def test_verificar_con_asiento(self):
        client.post("/asientos", json={
            "empresa_id": EMPRESA,
            "caso_id": CASO_ID,
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
