# -*- coding: utf-8 -*-
"""Tests de transiciones BORRADOR -> VISADO -> APROBADO -> RIZOMIZADO."""
import psycopg
import pytest
from fastapi.testclient import TestClient

from conta_rizoma4.api.main import app
from conta_rizoma4.custodia.repositorios import PG_URL


client = TestClient(app)
EMPRESA = "TEST_TRANS"
OBRA = "TEST_TRANS_OBRA"


def _limpiar():
    with psycopg.connect(PG_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM linea_asiento WHERE empresa_id = %s", (EMPRESA,))
            cur.execute("DELETE FROM asiento_contable WHERE empresa_id = %s", (EMPRESA,))
            cur.execute("DELETE FROM leases WHERE empresa_id = %s", (EMPRESA,))
            cur.execute("DELETE FROM obras WHERE empresa_id = %s", (EMPRESA,))
        conn.commit()


@pytest.fixture
def limpio():
    _limpiar()
    yield
    _limpiar()


class TestTransiciones:
    def test_flujo_completo(self, limpio):
        # 1. Crear obra
        r = client.post("/obras", json={
            "obra_id": OBRA, "empresa_id": EMPRESA, "nombre": "X",
        })
        assert r.status_code == 201, r.text
        # 2. Pedir lease
        r = client.post("/leases", json={
            "empresa_id": EMPRESA, "obra_id": OBRA,
            "operario": "op_01", "duracion_min": 60,
        })
        assert r.status_code == 201, r.text
        lease_id = r.json()["lease_id"]
        # 3. Crear asiento con lease
        r = client.post("/asientos", json={
            "empresa_id": EMPRESA,
            "codigo_acto": "A_COBRO_CLIENTE_TRANSF",
            "fecha": "2025-04-15",
            "concepto": "Cobro test",
            "creado_por": "op_01",
            "lease_id": lease_id,
            "obra_id": OBRA,
            "parametros": {
                "importe_centimos": 100000,
                "cliente_nif": "B12345678",
            },
        })
        assert r.status_code == 201, r.text
        indice = r.json()["indice"]
        # 4. Visar
        r = client.post(
            f"/asientos/{indice}/visar?empresa_id={EMPRESA}",
            json={"operario_visador": "jefe_obra"},
        )
        assert r.status_code == 200, r.text
        # 5. Aprobar
        r = client.post(
            f"/asientos/{indice}/aprobar?empresa_id={EMPRESA}",
            json={"operario_aprobador": "jefe_prod"},
        )
        assert r.status_code == 200, r.text
        # 6. Rizomizar
        r = client.post(
            f"/asientos/{indice}/rizomizar?empresa_id={EMPRESA}",
            json={"ok": True},
        )
        assert r.status_code == 200, r.text
        assert r.json()["estado"] == "RIZOMIZADO"

    def test_visar_sin_ser_borrador_falla(self, limpio):
        client.post("/obras", json={
            "obra_id": OBRA, "empresa_id": EMPRESA, "nombre": "X",
        })
        lease = client.post("/leases", json={
            "empresa_id": EMPRESA, "obra_id": OBRA, "operario": "op_01",
        }).json()
        r = client.post("/asientos", json={
            "empresa_id": EMPRESA,
            "codigo_acto": "A_COBRO_CLIENTE_TRANSF",
            "fecha": "2025-04-15",
            "concepto": "X",
            "creado_por": "op_01",
            "lease_id": lease["lease_id"],
            "parametros": {"importe_centimos": 100000, "cliente_nif": "B1"},
        })
        assert r.status_code == 201, r.text
        indice = r.json()["indice"]
        # Visar dos veces -> la segunda falla
        r1 = client.post(f"/asientos/{indice}/visar?empresa_id={EMPRESA}",
                         json={"operario_visador": "jefe"})
        assert r1.status_code == 200
        r2 = client.post(f"/asientos/{indice}/visar?empresa_id={EMPRESA}",
                         json={"operario_visador": "jefe"})
        assert r2.status_code == 409
