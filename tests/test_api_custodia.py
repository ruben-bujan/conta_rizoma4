# -*- coding: utf-8 -*-
"""Tests de endpoints de custodia (leases, obras, operarios, documentos)."""
import pytest
from fastapi.testclient import TestClient

from conta_rizoma4.api.main import app
from conta_rizoma4.custodia.repositorios import (
    RepositorioObra, RepositorioOperario, RepositorioLease, PG_URL,
)
import psycopg


client = TestClient(app)
EMPRESA = "TEST_API_CUST"
OBRA = "TEST_API_OBRA"
OPERARIO = "TEST_API_OP"


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
        r2 = client.get(f"/obras?empresa_id={EMPRESA}")
        assert r2.status_code == 200
        assert len(r2.json()) == 1


class TestOperarios:
    def test_crear(self, limpio):
        r = client.post("/operarios", json={
            "operario_id": OPERARIO, "empresa_id": EMPRESA,
            "nombre": "Ana", "rol": "aux_obra",
        })
        assert r.status_code == 201


class TestLeases:
    def test_solicitar_y_renovar(self, limpio):
        # Crear obra primero
        client.post("/obras", json={
            "obra_id": OBRA, "empresa_id": EMPRESA, "nombre": "X",
        })
        r = client.post("/leases", json={
            "empresa_id": EMPRESA, "obra_id": OBRA,
            "operario": OPERARIO, "duracion_min": 60,
        })
        assert r.status_code == 201, r.text
        lease = r.json()
        assert lease["estado"] == "CONCEDIDO"
        # Renovar
        r2 = client.post(f"/leases/{lease['lease_id']}/renovar",
                         json={"duracion_min": 120})
        assert r2.status_code == 200

    def test_cancelar(self, limpio):
        client.post("/obras", json={
            "obra_id": OBRA, "empresa_id": EMPRESA, "nombre": "X",
        })
        lease = client.post("/leases", json={
            "empresa_id": EMPRESA, "obra_id": OBRA,
            "operario": OPERARIO,
        }).json()
        r = client.post(f"/leases/{lease['lease_id']}/cancelar")
        assert r.status_code == 200
