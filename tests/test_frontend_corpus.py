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
    email = "frontend_corpus@example.com"
    sembrar_usuario(usuario_id="USER_FRONT", email=email,
                    password="test-password-1234", nombre="Frontend Corpus Tester",
                    rol="admin", empresa_id="TEST_EMP")
    r = client.post("/auth/login", json={
        "email": email,
        "password": "test-password-1234",
    })
    if r.status_code == 200:
        token = r.json()["access_token"]
        client.headers["Authorization"] = f"Bearer {token}"


class TestFrontendCorpus:
    def test_corpus_endpoint_agregado(self):
        r = client.get("/corpus/agregado")
        assert r.status_code == 200, r.text

    def test_corpus_endpoint_patrones(self):
        r = client.get("/corpus/patrones")
        assert r.status_code == 200, r.text
