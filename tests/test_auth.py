# -*- coding: utf-8 -*-
"""Tests de autenticación."""
import psycopg
import pytest
from fastapi.testclient import TestClient

from conta_rizoma4.api.main import app
from conta_rizoma4.custodia.repositorios import PG_URL


client = TestClient(app)
EMPRESA = "TEST_AUTH"
EMAIL = "test_auth@example.com"
USUARIO_ID = "TEST_AUTH_USER"


def _limpiar():
    with psycopg.connect(PG_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM usuarios WHERE email = %s", (EMAIL,))
        conn.commit()


@pytest.fixture
def limpio():
    _limpiar()
    yield
    _limpiar()


class TestAuth:
    def test_registro(self, limpio):
        r = client.post("/auth/registro", json={
            "usuario_id": USUARIO_ID, "email": EMAIL,
            "password": "test1234", "nombre": "Test User",
            "rol": "aux_obra", "empresa_id": EMPRESA,
        })
        assert r.status_code == 201, r.text

    def test_login(self, limpio):
        client.post("/auth/registro", json={
            "usuario_id": USUARIO_ID, "email": EMAIL,
            "password": "test1234", "nombre": "Test",
            "rol": "aux_obra", "empresa_id": EMPRESA,
        })
        r = client.post("/auth/login", json={
            "email": EMAIL, "password": "test1234",
        })
        assert r.status_code == 200, r.text
        assert "access_token" in r.json()

    def test_login_mal_password(self, limpio):
        client.post("/auth/registro", json={
            "usuario_id": USUARIO_ID, "email": EMAIL,
            "password": "test1234", "nombre": "Test",
            "rol": "aux_obra", "empresa_id": EMPRESA,
        })
        r = client.post("/auth/login", json={
            "email": EMAIL, "password": "wrong",
        })
        assert r.status_code == 401

    def test_me_sin_token_falla(self):
        r = client.get("/auth/me")
        assert r.status_code == 401

    def test_me_con_token(self, limpio):
        client.post("/auth/registro", json={
            "usuario_id": USUARIO_ID, "email": EMAIL,
            "password": "test1234", "nombre": "Test",
            "rol": "aux_obra", "empresa_id": EMPRESA,
        })
        login = client.post("/auth/login", json={
            "email": EMAIL, "password": "test1234",
        }).json()
        token = login["access_token"]
        r = client.get("/auth/me",
                       headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
