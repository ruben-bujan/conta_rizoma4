# -*- coding: utf-8 -*-
"""Tests de custodia: obras, operarios, leases, documentos."""
from datetime import date

import psycopg
import pytest

from conta_rizoma4.custodia.modelo import Obra, Operario, CustodiaError
from conta_rizoma4.custodia.repositorios import (
    RepositorioObra, RepositorioOperario, RepositorioLease,
    RepositorioDocumento, PG_URL,
)


EMPRESA = "TEST_CUSTODIA_EMP"
OBRA = "TEST_OBRA_001"
OPERARIO = "TEST_OP_001"


def _limpiar():
    with psycopg.connect(PG_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM leases WHERE empresa_id = %s", (EMPRESA,))
            cur.execute("DELETE FROM documentos WHERE empresa_id = %s", (EMPRESA,))
            cur.execute("DELETE FROM operarios WHERE empresa_id = %s", (EMPRESA,))
            cur.execute("DELETE FROM obras WHERE empresa_id = %s", (EMPRESA,))
        conn.commit()


@pytest.fixture
def limpio():
    _limpiar()
    yield
    _limpiar()


class TestObra:
    def test_crear(self, limpio):
        repo = RepositorioObra()
        obra = Obra(
            obra_id=OBRA, empresa_id=EMPRESA,
            nombre="Autovía AII",
            cliente_nif="MFOM",
            presupuesto_centimos=923000000,
            fecha_inicio=date(2006, 9, 1),
            fecha_fin=date(2008, 5, 31),
        )
        repo.crear(obra)
        d = repo.obtener(OBRA)
        assert d is not None
        assert d["nombre"] == "Autovía AII"
        assert d["cliente_nif"] == "MFOM"


class TestOperario:
    def test_crear(self, limpio):
        repo = RepositorioOperario()
        op = Operario(
            operario_id=OPERARIO, empresa_id=EMPRESA,
            nombre="Ana García", rol="aux_obra",
            email="ana@example.com",
        )
        repo.crear(op)
        d = repo.obtener(OPERARIO)
        assert d is not None
        assert d["rol"] == "aux_obra"


class TestLease:
    def test_solicitar(self, limpio):
        # Crear obra primero (FK)
        RepositorioObra().crear(Obra(
            obra_id=OBRA, empresa_id=EMPRESA, nombre="X",
        ))
        repo = RepositorioLease()
        lease = repo.solicitar(
            empresa_id=EMPRESA, obra_id=OBRA, tipo="asiento",
            operario=OPERARIO, duracion_min=60,
        )
        assert "lease_id" in lease
        assert lease["indice_reservado"] >= 0
        assert lease["estado"] == "CONCEDIDO"

    def test_renovar(self, limpio):
        RepositorioObra().crear(Obra(obra_id=OBRA, empresa_id=EMPRESA, nombre="X"))
        repo = RepositorioLease()
        lease = repo.solicitar(EMPRESA, OBRA, "asiento", OPERARIO, 60)
        renovado = repo.renovar(lease["lease_id"], 120)
        assert renovado["renovado_en"] is not None

    def test_cancelar(self, limpio):
        RepositorioObra().crear(Obra(obra_id=OBRA, empresa_id=EMPRESA, nombre="X"))
        repo = RepositorioLease()
        lease = repo.solicitar(EMPRESA, OBRA, "asiento", OPERARIO, 60)
        repo.cancelar(lease["lease_id"])
        d = repo.obtener(lease["lease_id"])
        assert d["estado"] == "CANCELADO"

    def test_dos_leases_indices_distintos(self, limpio):
        RepositorioObra().crear(Obra(obra_id=OBRA, empresa_id=EMPRESA, nombre="X"))
        repo = RepositorioLease()
        l1 = repo.solicitar(EMPRESA, OBRA, "asiento", OPERARIO, 60)
        l2 = repo.solicitar(EMPRESA, OBRA, "asiento", OPERARIO, 60)
        assert l1["indice_reservado"] != l2["indice_reservado"]


class TestDocumento:
    def test_crear(self, limpio):
        RepositorioObra().crear(Obra(obra_id=OBRA, empresa_id=EMPRESA, nombre="X"))
        repo = RepositorioDocumento()
        hash_fake = "a" * 64
        doc = repo.crear(
            empresa_id=EMPRESA, hash_cas=hash_fake, tipo="FACTURA_RECIBIDA",
            obra_id=OBRA, nombre="factura.pdf", tamano_bytes=12345,
            subido_por=OPERARIO,
        )
        assert doc["hash_cas"] == hash_fake
        # Idempotente
        doc2 = repo.crear(
            empresa_id=EMPRESA, hash_cas=hash_fake, tipo="FACTURA_RECIBIDA",
        )
        assert doc2["id"] == doc["id"]
