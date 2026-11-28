# -*- coding: utf-8 -*-
"""Tests de autenticación."""
import psycopg
import pytest
from fastapi.testclient import TestClient

from conta_rizoma4.api.main import app
from conta_rizoma4.custodia.repositorios import PG_URL
from test_helpers_auth import sembrar_usuario


client = TestClient(app)
EMPRESA = "TEST_AUTH"
EMAIL = "test_auth@example.com"
USUARIO_ID = "TEST_AUTH_USER"
ADMIN_EMAIL = "test_auth_admin@example.com"
ADMIN_ID = "TEST_AUTH_ADMIN"
PASSWORD = "test-password-1234"


def _limpiar():
    with psycopg.connect(PG_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM usuarios WHERE email = ANY(%s)", ([EMAIL, ADMIN_EMAIL],))
        conn.commit()


@pytest.fixture
def limpio():
    _limpiar()
    sembrar_usuario(usuario_id=ADMIN_ID, email=ADMIN_EMAIL, password=PASSWORD,
                    nombre="Test Admin", rol="admin", empresa_id=EMPRESA)
    login = client.post("/auth/login", json={"email": ADMIN_EMAIL, "password": PASSWORD}).json()
    client.headers["Authorization"] = f"Bearer {login['access_token']}"
    yield
    client.headers.pop("Authorization", None)
    _limpiar()


def _registrar_usuario():
    return client.post("/auth/registro", json={
        "usuario_id": USUARIO_ID, "email": EMAIL, "password": PASSWORD,
        "nombre": "Test User", "rol": "aux_obra",
    })


class TestAuth:
    def test_registro(self, limpio):
        r = _registrar_usuario()
        assert r.status_code == 201, r.text
        assert r.json()["empresa_id"] == EMPRESA

    def test_login(self, limpio):
        _registrar_usuario()
        r = client.post("/auth/login", json={
            "email": EMAIL, "password": PASSWORD,
        })
        assert r.status_code == 200, r.text
        assert "access_token" in r.json()

    def test_login_mal_password(self, limpio):
        _registrar_usuario()
        r = client.post("/auth/login", json={
            "email": EMAIL, "password": "wrong-password",
        })
        assert r.status_code == 401

    def test_me_sin_token_falla(self):
        r = client.get("/auth/me")
        assert r.status_code == 401

    def test_me_con_token(self, limpio):
        _registrar_usuario()
        login = client.post("/auth/login", json={
            "email": EMAIL, "password": PASSWORD,
        }).json()
        token = login["access_token"]
        r = client.get("/auth/me",
                       headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200

    def test_no_permite_autoalta_admin_ni_empresa_en_payload(self, limpio):
        respuesta = client.post("/auth/registro", json={
            "usuario_id": "EVIL", "email": "evil@example.com", "password": PASSWORD,
            "nombre": "Evil", "rol": "admin", "empresa_id": "OTRA_EMPRESA",
        })
        assert respuesta.status_code == 422
