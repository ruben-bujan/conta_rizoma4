# -*- coding: utf-8 -*-
"""Tests de la API de corpus forense."""
import psycopg
import pytest
from fastapi.testclient import TestClient

from conta_rizoma4.api.main import app
from conta_rizoma4.custodia.repositorios import PG_URL


client = TestClient(app)


def _limpiar():
    with psycopg.connect(PG_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM danos WHERE expediente_id LIKE 'TEST_API_%'")
            cur.execute("DELETE FROM flujos WHERE expediente_id LIKE 'TEST_API_%'")
            cur.execute("DELETE FROM expedientes WHERE expediente_id LIKE 'TEST_API_%'")
            cur.execute("DELETE FROM sujetos WHERE sujeto_id LIKE 'TEST_API_%'")
        conn.commit()


@pytest.fixture
def limpio():
    _limpiar()
    yield
    _limpiar()


class TestApiCorpus:
    def test_crear_sujeto(self, limpio):
        r = client.post("/corpus/sujetos", json={
            "sujeto_id": "TEST_API_S1", "tipo": "MIPYME",
            "nombre": "Test SL", "sector": "construccion",
        })
        assert r.status_code == 201, r.text
        assert r.json()["tipo"] == "MIPYME"

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
        d = r.json()
        assert d["universo"] == "U1"

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
        d = r.json()
        assert d["principal_debido_centimos"] == 1000000
        assert d["dano_total_centimos"] > 1000000

    def test_agregado(self, limpio):
        r = client.get("/corpus/agregado")
        assert r.status_code == 200

    def test_patrones(self, limpio):
        r = client.get("/corpus/patrones")
        assert r.status_code == 200
        assert "alertas" in r.json()
