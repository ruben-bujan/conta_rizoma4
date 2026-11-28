# -*- coding: utf-8 -*-
"""Configuración global de fixtures para Pytest."""
from __future__ import annotations

import psycopg
import pytest
from fastapi.testclient import TestClient

from conta_rizoma4.api.main import app
from conta_rizoma4.partida_doble.persistencia import PG_URL
from test_helpers_auth import sembrar_usuario


@pytest.fixture(autouse=True)
def _autenticar_cliente_api(request):
    """Inyecta automáticamente un token Bearer válido en el TestClient para los tests de API."""
    # Solo aplicar en tests que pertenezcan al directorio o módulos de API
    if "api" in request.node.nodeid or "frontend_corpus" in request.node.nodeid:
        email = "test_global_auth@example.com"
        usuario_id = "TEST_GLOBAL_USER"
        empresa_id = "TEST_API_EMPRESA"

        client = TestClient(app)
        with psycopg.connect(PG_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM usuarios WHERE email = %s", (email,))
            conn.commit()

        sembrar_usuario(usuario_id=usuario_id, email=email,
                        password="test-password-1234", nombre="Global Test User",
                        rol="admin", empresa_id=empresa_id)
        r_login = client.post("/auth/login", json={
            "email": email,
            "password": "test-password-1234",
        })
        if r_login.status_code == 200:
            token = r_login.json()["access_token"]
            # Inyectar en los clientes de test que usen TestClient(app)
            # Modificamos el cliente global de test si existe en los módulos
            for module_name in ["tests.test_api", "tests.test_api_corpus", "tests.test_api_custodia", "tests.test_api_transiciones", "tests.test_frontend_corpus"]:
                mod = request.config.pluginmanager.get_plugin(module_name) or __import__(module_name, fromlist=["client"])
                if hasattr(mod, "client"):
                    mod.client.headers["Authorization"] = f"Bearer {token}"
