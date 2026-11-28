# -*- coding: utf-8 -*-
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from conta_rizoma4.api.main import app
from test_helpers_auth import sembrar_usuario

client = TestClient(app)


@pytest.fixture(autouse=True)
def _setup_auth():
    """Autentica automáticamente el cliente para todas las pruebas de este módulo."""
    email = "corpus_test@example.com"
    sembrar_usuario(usuario_id="USER_CORPUS", email=email,
                    password="test-password-1234", nombre="Corpus Tester",
                    rol="admin", empresa_id="TEST_EMP")
    r = client.post("/auth/login", json={
        "email": email,
        "password": "test-password-1234",
    })
    if r.status_code == 200:
        token = r.json()["access_token"]
        client.headers["Authorization"] = f"Bearer {token}"


@pytest.fixture
def limpio():
    # Limpieza o setup específico si lo requiere
    yield


class TestApiCorpus:
    def test_crear_sujeto(self, limpio):
        r = client.post("/corpus/sujetos", json={
            "sujeto_id": "TEST_API_S1", "tipo": "MIPYME",
            "nombre": "Test SL", "sector": "construccion",
        })
        assert r.status_code == 201, r.text

    def test_crear_expediente(self, limpio):
        client.post("/corpus/sujetos", json={
            "sujeto_id": "TEST_API_S1", "tipo": "MIPYME",
            "nombre": "Test SL", "sector": "construccion",
        })
        r = client.post("/corpus/expedientes", json={
            "expediente_id": "TEST_API_E1", "sujeto_id": "TEST_API_S1",
            "via_u1": "V1", "estado_concurso": "recaydo",
            "seccion_sexta": False, "calificacion": "fortuito",
            "buena_fe_acreditada": True,
            "porcentaje_menoscabo": 100.0, "quiebra_modo_vida": True,
        })
        assert r.status_code == 201, r.text

    def test_flujo_y_dano(self, limpio):
        client.post("/corpus/sujetos", json={
            "sujeto_id": "TEST_API_S1", "tipo": "MIPYME",
            "nombre": "Test SL", "sector": "construccion",
        })
        client.post("/corpus/expedientes", json={
            "expediente_id": "TEST_API_E1", "sujeto_id": "TEST_API_S1",
            "via_u1": "V1", "estado_concurso": "recaydo",
            "seccion_sexta": False, "calificacion": "fortuito",
            "buena_fe_acreditada": True,
            "porcentaje_menoscabo": 100.0,
            "fecha_inicio": "2013-01-01",
        })
        client.post("/corpus/flujos", json={
            "expediente_id": "TEST_API_E1", "fecha": "2013-01-01",
            "concepto": "Factura", "importe_centimos": 1000000,
            "categoria": "factura",
        })
        client.post("/corpus/flujos", json={
            "expediente_id": "TEST_API_E1", "fecha": "2013-06-01",
            "concepto": "Renuncia", "importe_centimos": 0,
            "categoria": "renuncia_interes",
        })
        r = client.post(
            "/corpus/expedientes/TEST_API_E1/calcular-dano",
            params={"fecha_corte": "2018-11-30"},
        )
        assert r.status_code == 200, r.text

    def test_agregado(self, limpio):
        r = client.get("/corpus/agregado")
        assert r.status_code == 200, r.text

    def test_patrones(self, limpio):
        r = client.get("/corpus/patrones")
        assert r.status_code == 200, r.text
