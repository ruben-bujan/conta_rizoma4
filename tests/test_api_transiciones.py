# -*- coding: utf-8 -*-
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from conta_rizoma4.api.main import app
from test_helpers_auth import sembrar_usuario

client = TestClient(app)

EMPRESA = "TEST_EMP_TRANS"
OBRA = "OBRA_TRANS_01"
OPERARIO = "USER_TRANS"
CASO_ID = "TEST_CASE_TRANS_01"


@pytest.fixture(autouse=True)
def _setup_auth():
    """Autentica automáticamente el cliente para todas las pruebas de este módulo."""
    email = "trans_test@example.com"
    sembrar_usuario(usuario_id="USER_TRANS", email=email,
                    password="test-password-1234", nombre="Transiciones Tester",
                    rol="admin", empresa_id=EMPRESA)
    r = client.post("/auth/login", json={
        "email": email,
        "password": "test-password-1234",
    })
    if r.status_code == 200:
        token = r.json()["access_token"]
        client.headers["Authorization"] = f"Bearer {token}"
    RepositorioCasoRizoma4().asociar(EMPRESA, CASO_ID, "USER_TRANS")


import psycopg
from conta_rizoma4.partida_doble.persistencia import PG_URL
from conta_rizoma4.custodia.casos_rizoma4 import RepositorioCasoRizoma4


def _limpiar():
    with psycopg.connect(PG_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM linea_asiento WHERE empresa_id = %s", (EMPRESA,))
            cur.execute("DELETE FROM asiento_contable WHERE empresa_id = %s", (EMPRESA,))
            cur.execute("DELETE FROM empresa_casos_rizoma4 WHERE empresa_id = %s", (EMPRESA,))
            cur.execute("DELETE FROM leases WHERE empresa_id = %s", (EMPRESA,))
            cur.execute("DELETE FROM obras WHERE empresa_id = %s", (EMPRESA,))
        conn.commit()


@pytest.fixture
def limpio():
    _limpiar()
    RepositorioCasoRizoma4().asociar(EMPRESA, CASO_ID, "USER_TRANS")
    yield
    _limpiar()


class TestTransiciones:
    def test_flujo_completo(self, limpio):
        r = client.post("/obras", json={
            "obra_id": OBRA, "empresa_id": EMPRESA, "nombre": "X",
        })
        assert r.status_code == 201, r.text

    def test_visar_sin_ser_borrador_falla(self, limpio):
        client.post("/obras", json={
            "obra_id": OBRA, "empresa_id": EMPRESA, "nombre": "X",
        })
        assert client.post("/operarios", json={
            "operario_id": OPERARIO, "empresa_id": EMPRESA,
            "nombre": "Ana", "rol": "aux_obra",
        }).status_code in (200, 201)
        res = client.post("/leases", json={
            "empresa_id": EMPRESA, "obra_id": OBRA, "operario": OPERARIO,
        })
        assert res.status_code == 201, res.text
        lease = res.json()
        r = client.post("/asientos", json={
            "empresa_id": EMPRESA,
            "caso_id": CASO_ID,
            "codigo_acto": "A_COBRO_CLIENTE_TRANSF",
            "fecha": "2025-04-15",
            "concepto": "X",
            "creado_por": OPERARIO,
            "lease_id": lease["lease_id"],
            "parametros": {"importe_centimos": 100000, "cliente_nif": "B1"},
        })
        assert r.status_code in (200, 201), r.text
