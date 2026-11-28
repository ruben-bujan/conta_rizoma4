# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime, timezone

import psycopg
import pytest
from fastapi.testclient import TestClient

from conta_rizoma4.api.main import app
from conta_rizoma4.custodia.casos_rizoma4 import RepositorioCasoRizoma4
from conta_rizoma4.dominio.adaptadores.repositorio_postgres import RepositorioPermisosEvento
from conta_rizoma4.partida_doble.persistencia import PG_URL
from test_helpers_auth import sembrar_usuario

pytestmark = pytest.mark.integration

client = TestClient(app)

EMPRESA = "TEST_EMP_DELEG"
CASO_ID = "TEST_CASE_DELEG"
OPERARIO = "USER_DELEG"
JEFE = "JEFE_DELEG"
PERMISO_ID = "PERM_DELEG_DIARIO"
OBRA = "OBRA_DELEG_01"
CASO = "CASO_DELEG_01"
LEASE_ID = ""


def _token(usuario_id: str, email: str, rol: str) -> str:
    sembrar_usuario(
        usuario_id=usuario_id,
        email=email,
        password="test-password-1234",
        nombre=usuario_id,
        rol=rol,
        empresa_id=EMPRESA,
    )
    respuesta = client.post("/auth/login", json={
        "email": email,
        "password": "test-password-1234",
    })
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()["access_token"]


def _limpiar() -> None:
    with psycopg.connect(PG_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM dominio_evento WHERE entidad_id = %s", (EMPRESA,))
            cur.execute("DELETE FROM linea_asiento WHERE empresa_id = %s", (EMPRESA,))
            cur.execute("DELETE FROM asiento_contable WHERE empresa_id = %s", (EMPRESA,))
            cur.execute("DELETE FROM empresa_casos_rizoma4 WHERE empresa_id = %s", (EMPRESA,))
            cur.execute("DELETE FROM leases WHERE empresa_id = %s", (EMPRESA,))
            cur.execute("DELETE FROM obras WHERE empresa_id = %s", (EMPRESA,))
        conn.commit()


@pytest.fixture(autouse=True)
def _setup():
    admin_token = _token("ADMIN_DELEG", "admin_deleg@example.com", "admin")
    _token(OPERARIO, "operario_deleg@example.com", "aux_obra")
    client.headers["Authorization"] = f"Bearer {admin_token}"
    _limpiar()
    RepositorioCasoRizoma4().asociar(EMPRESA, CASO, "ADMIN_DELEG")
    assert client.post("/obras", json={
        "obra_id": OBRA, "empresa_id": EMPRESA, "nombre": "Obra delegada",
    }).status_code == 201
    assert client.post("/operarios", json={
        "operario_id": OPERARIO, "empresa_id": EMPRESA,
        "nombre": "Operario delegado", "rol": "aux_obra",
    }).status_code in (200, 201)
    arrendamiento = client.post("/leases", json={
        "empresa_id": EMPRESA, "obra_id": OBRA, "operario": OPERARIO,
    })
    assert arrendamiento.status_code == 201, arrendamiento.text
    global LEASE_ID
    LEASE_ID = arrendamiento.json()["lease_id"]
    yield
    _limpiar()


def _asiento() -> dict:
    return {
        "empresa_id": EMPRESA,
        "caso_id": CASO,
        "codigo_acto": "A_COBRO_CLIENTE_TRANSF",
        "fecha": "2025-04-15",
        "concepto": "Delegación de asiento",
        "creado_por": OPERARIO,
        "lease_id": LEASE_ID,
        "parametros": {"importe_centimos": 100000, "cliente_nif": "B1"},
    }


def _conceder() -> None:
    RepositorioPermisosEvento().conceder(
        entidad_id=EMPRESA,
        permiso_id=PERMISO_ID,
        otorgante_id=JEFE,
        otorgante_rol="JEFE_CONTABILIDAD",
        beneficiario_id=OPERARIO,
        beneficiario_rol="AUXILIAR",
        competencia="ASIENTO_DIARIO",
        alcance=EMPRESA,
        otorgada_en=datetime.now(timezone.utc),
    )


def _token_operario() -> str:
    return _token(OPERARIO, "operario_deleg@example.com", "aux_obra")


def test_auxiliar_sin_delegacion_no_crea_asiento():
    client.headers["Authorization"] = f"Bearer {_token_operario()}"
    respuesta = client.post("/asientos", json=_asiento())
    assert respuesta.status_code == 403, respuesta.text


def test_delegacion_en_dominio_evento_permite_crear_asiento():
    _conceder()
    client.headers["Authorization"] = f"Bearer {_token_operario()}"
    respuesta = client.post("/asientos", json=_asiento())
    assert respuesta.status_code == 201, respuesta.text


def test_revocacion_en_dominio_evento_bloquea_creacion_posterior():
    _conceder()
    RepositorioPermisosEvento().revocar(
        entidad_id=EMPRESA,
        permiso_id=PERMISO_ID,
        actor_id=JEFE,
        motivo="Revocación de prueba",
        revocada_en=datetime.now(timezone.utc),
    )
    client.headers["Authorization"] = f"Bearer {_token_operario()}"
    respuesta = client.post("/asientos", json=_asiento())
    assert respuesta.status_code == 403, respuesta.text
