# -*- coding: utf-8 -*-
"""Tests del corpus forense: clasificación + cálculo de daño."""
from datetime import date

import psycopg
import pytest

from conta_rizoma4.corpus_forense.modelo import (
    Expediente, Flujo, Sujeto, Dano,
    clasificar_expediente, calcular_dano,
)
from conta_rizoma4.corpus_forense.repositorios import (
    RepositorioSujeto, RepositorioExpediente, RepositorioFlujo,
    RepositorioDano, PG_URL,
)


class TestClasificacion:
    def test_u1_concurso_ok(self):
        e = Expediente(
            expediente_id="E1", sujeto_id="S1",
            via_u1="V1", estado_concurso="recaydo",
            seccion_sexta=False, calificacion="fortuito",
            buena_fe_acreditada=True,
            porcentaje_menoscabo=100.0,
            quiebra_modo_vida=True,
        )
        u, r = clasificar_expediente(e)
        assert u == "U1"
        assert r == "restiucion_in_integrum_maxima"

    def test_u1_punta_de_lanza(self):
        e = Expediente(
            expediente_id="E1", sujeto_id="S1",
            via_u1="V3", es_punta_de_lanza=True,
            estado_concurso="recaydo", seccion_sexta=False,
            calificacion="fortuito",
            buena_fe_acreditada=True, porcentaje_menoscabo=100.0,
        )
        u, r = clasificar_expediente(e)
        assert u == "U1"

    def test_u2_sin_concurso(self):
        e = Expediente(
            expediente_id="E2", sujeto_id="S2",
            estado_concurso="ninguno",
            buena_fe_acreditada=True,
            porcentaje_menoscabo=25.0,
        )
        u, r = clasificar_expediente(e)
        assert u == "U2"

    def test_u3_sin_relevancia(self):
        e = Expediente(
            expediente_id="E3", sujeto_id="S3",
            estado_concurso="ninguno",
            buena_fe_acreditada=True,
            porcentaje_menoscabo=10.0,
        )
        u, r = clasificar_expediente(e)
        assert u == "U3"

    def test_no_victima_sin_buena_fe(self):
        e = Expediente(
            expediente_id="E4", sujeto_id="S4",
            estado_concurso="ninguno",
            buena_fe_acreditada=False,
            porcentaje_menoscabo=15.0,
        )
        u, r = clasificar_expediente(e)
        assert u == "no_victima"

    def test_u2_concurso_culpable(self):
        e = Expediente(
            expediente_id="E5", sujeto_id="S5",
            estado_concurso="recaydo",
            seccion_sexta=True, calificacion="culpable",
            buena_fe_acreditada=True, porcentaje_menoscabo=30.0,
        )
        u, r = clasificar_expediente(e)
        assert u == "U2"

    def test_no_diligente(self):
        e = Expediente(
            expediente_id="E6", sujeto_id="S6",
            estado_concurso="recaydo",
            incidente_concursal_por_no_diligencia=True,
            buena_fe_acreditada=True, porcentaje_menoscabo=30.0,
        )
        u, r = clasificar_expediente(e)
        # Sin diligencia, no es U1
        assert u != "U1"


class TestCalculoDano:
    def test_calcular_dano_basico(self):
        e = Expediente(
            expediente_id="E1", sujeto_id="S1",
            fecha_inicio=date(2013, 1, 1), fecha_fin=date(2015, 5, 29),
        )
        flujos = [
            Flujo(id=1, expediente_id="E1", fecha=date(2013, 1, 1),
                  concepto="Factura", importe_centimos=1_000_000,
                  categoria="factura"),
            Flujo(id=2, expediente_id="E1", fecha=date(2013, 6, 1),
                  concepto="Renuncia interés", importe_centimos=0,
                  categoria="renuncia_interes"),
        ]
        d = calcular_dano(e, flujos, date(2018, 11, 30))
        assert d.principal_debido_centimos == 1_000_000
        assert d.interes_renunciado_centimos > 0
        assert d.interes_compuesto_centimos > 0
        assert d.dano_total_centimos > 1_000_000


class TestRepositorios:
    def test_crear_sujeto(self):
        repo = RepositorioSujeto()
        try:
            repo.crear(Sujeto(
                sujeto_id="TEST_SUJ", tipo="MIPYME",
                nombre="Test SL", sector="construccion",
            ))
            d = repo.obtener("TEST_SUJ")
            assert d is not None
            assert d["tipo"] == "MIPYME"
        finally:
            with psycopg.connect(PG_URL) as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM sujetos WHERE sujeto_id='TEST_SUJ'")
                conn.commit()
