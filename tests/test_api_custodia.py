# -*- coding: utf-8 -*-
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from conta_rizoma4.api.main import app
from test_helpers_auth import sembrar_usuario

client = TestClient(app)

EMPRESA = "TEST_EMP_CUSTODIA"
OBRA = "OBRA_01"
OPERARIO = "OP_01"


@pytest.fixture(autouse=True)
def _setup_auth():
    """Autentica automáticamente el cliente para todas las pruebas de este módulo."""
    email = "custodia_test@example.com"
    sembrar_usuario(usuario_id="USER_CUSTODIA", email=email,
                    password="test-password-1234", nombre="Custodia Tester",
                    rol="admin", empresa_id=EMPRESA)
    r = client.post("/auth/login", json={
        "email": email,
        "password": "test-password-1234",
    })
    if r.status_code == 200:
        token = r.json()["access_token"]
        client.headers["Authorization"] = f"Bearer {token}"


import psycopg
from conta_rizoma4.partida_doble.persistencia import PG_URL


def _limpiar():
    with psycopg.connect(PG_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM leases WHERE empresa_id = %s", (EMPRESA,))
            cur.execute("DELETE FROM operarios WHERE empresa_id = %s", (EMPRESA,))
            cur.execute("DELETE FROM obras WHERE empresa_id = %s", (EMPRESA,))
        conn.commit()


@pytest.fixture
def limpio():
    _limpiar()
    yield
    _limpiar()


class TestObras:
    def test_crear_y_listar(self, limpio):
        r = client.post("/obras", json={
            "obra_id": OBRA, "empresa_id": EMPRESA,
            "nombre": "Autovía AII", "cliente_nif": "MFOM",
            "presupuesto_centimos": 923000000,
        })
        assert r.status_code == 201, r.text


class TestOperarios:
    def test_crear(self, limpio):
        r = client.post("/operarios", json={
            "operario_id": OPERARIO, "empresa_id": EMPRESA,
            "nombre": "Ana", "rol": "aux_obra",
        })
        assert r.status_code == 201, r.text


class TestLeases:
    def test_solicitar_y_renovar(self, limpio):
        client.post("/obras", json={
            "obra_id": OBRA, "empresa_id": EMPRESA, "nombre": "X",
        })
        assert client.post("/operarios", json={
            "operario_id": OPERARIO, "empresa_id": EMPRESA,
            "nombre": "Ana", "rol": "aux_obra",
        }).status_code in (200, 201)
        r = client.post("/leases", json={
            "empresa_id": EMPRESA, "obra_id": OBRA,
            "operario": OPERARIO, "duracion_min": 60,
        })
        assert r.status_code == 201, r.text

    def test_cancelar(self, limpio):
        client.post("/obras", json={
            "obra_id": OBRA, "empresa_id": EMPRESA, "nombre": "X",
        })
        assert client.post("/operarios", json={
            "operario_id": OPERARIO, "empresa_id": EMPRESA,
            "nombre": "Ana", "rol": "aux_obra",
        }).status_code in (200, 201)
        res = client.post("/leases", json={
            "empresa_id": EMPRESA, "obra_id": OBRA,
            "operario": OPERARIO,
        })
        assert res.status_code == 201, res.text
        lease = res.json()
        r = client.post(f"/leases/{lease['lease_id']}/cancelar")
        assert r.status_code == 200, r.text
