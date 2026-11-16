# -*- coding: utf-8 -*-
"""Tests de agregación del corpus forense."""
import psycopg
import pytest

from conta_rizoma4.corpus_forense.agregacion import (
    agregar_corpus, detectar_patrones, PG_URL,
)
from conta_rizoma4.corpus_forense.modelo import (
    Dano, Expediente, Sujeto,
)
from conta_rizoma4.corpus_forense.repositorios import (
    RepositorioSujeto, RepositorioExpediente, RepositorioDano,
)
from datetime import date


def _limpiar():
    with psycopg.connect(PG_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM danos")
            cur.execute("DELETE FROM flujos")
            cur.execute("DELETE FROM expedientes WHERE expediente_id LIKE 'TEST_%'")
            cur.execute("DELETE FROM sujetos WHERE sujeto_id LIKE 'TEST_%'")
        conn.commit()


@pytest.fixture
def datos():
    _limpiar()
    # Crear 3 sujetos + 3 expedientes + 3 daños
    repo_s = RepositorioSujeto()
    repo_e = RepositorioExpediente()
    repo_d = RepositorioDano()

    for i, (sector, universo, dano) in enumerate([
        ("construccion", "U1", 2_500_000_00),
        ("construccion", "U1", 1_500_000_00),
        ("construccion", "U1", 1_000_000_00),
        ("suministros", "U2", 500_000_00),
    ]):
        sid = f"TEST_S{i}"
        eid = f"TEST_E{i}"
        repo_s.crear(Sujeto(
            sujeto_id=sid, tipo="MIPYME", nombre=f"Empresa {i}",
            sector=sector,
        ))
        exp = Expediente(
            expediente_id=eid, sujeto_id=sid,
            estado_concurso="recaydo" if universo == "U1" else "ninguno",
            buena_fe_acreditada=True,
            porcentaje_menoscabo=100.0 if universo == "U1" else 25.0,
        )
        repo_e.crear(exp)
        repo_d.crear(Dano(
            expediente_id=eid,
            principal_debido_centimos=dano,
            interes_renunciado_centimos=dano // 10,
            interes_compuesto_centimos=dano // 5,
            dano_moral_centimos=0,
            consecuencias_indirectas_centimos=0,
            dano_total_centimos=dano,
            fecha_corte=date(2018, 11, 30),
        ))
    yield
    _limpiar()


class TestAgregacion:
    def test_agregar(self, datos):
        r = agregar_corpus()
        assert r["totales"]["n_expedientes"] == 4
        assert r["totales"]["dano_total"] > 0
        assert len(r["por_universo"]) >= 2

    def test_agregar_por_universo(self, datos):
        r = agregar_corpus(universo="U1")
        assert r["totales"]["n_expedientes"] == 3


class TestPatrones:
    def test_detectar(self, datos):
        r = detectar_patrones()
        assert "tasa_u1_por_sector" in r
        assert "tasa_seccion_sexta" in r
        assert "alertas" in r
        # Construcción con 100% U1 debe alertar
        alertas_construccion = [
            a for a in r["alertas"] if "construccion" in a.lower()
        ]
        assert len(alertas_construccion) > 0
