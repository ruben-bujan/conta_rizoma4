# -*- coding: utf-8 -*-
"""Tests del RepositorioActoEconomico."""
from __future__ import annotations

from datetime import date

import psycopg
import pytest

from conta_rizoma4.operativo.repositorio_acto import (
    PG_URL,
    ReporteCadena,
    RepositorioActoEconomico,
)


@pytest.fixture
def repo_limpio():
    """Repo con cleanup: borra los actos que el test cree."""
    repo = RepositorioActoEconomico()
    indice_inicial = repo.ultimo_indice()

    def _limpia():
        with psycopg.connect(PG_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM acto_economico WHERE indice > %s",
                    (indice_inicial,),
                )
            conn.commit()

    _limpia()
    yield repo
    _limpia()


class TestCreacion:
    def test_crear_siguiente_encadena(self, repo_limpio):
        a0 = repo_limpio.crear_siguiente(
            fecha=date(2025, 1, 1), cuenta_pgc="705",
            importe_centimos=100, concepto="A", creado_por="rubén",
        )
        a1 = repo_limpio.crear_siguiente(
            fecha=date(2025, 1, 2), cuenta_pgc="705",
            importe_centimos=200, concepto="B", creado_por="rubén",
        )
        a2 = repo_limpio.crear_siguiente(
            fecha=date(2025, 1, 3), cuenta_pgc="705",
            importe_centimos=300, concepto="C", creado_por="rubén",
        )
        assert a1.hash_previo == a0.hash
        assert a2.hash_previo == a1.hash
        assert a1.indice == a0.indice + 1
        assert a2.indice == a1.indice + 1

    def test_ultimo_indice(self, repo_limpio):
        a = repo_limpio.crear_siguiente(
            fecha=date(2025, 1, 1), cuenta_pgc="705",
            importe_centimos=100, concepto="X", creado_por="rubén",
        )
        assert repo_limpio.ultimo_indice() == a.indice


class TestLectura:
    def test_obtener_existente(self, repo_limpio):
        a = repo_limpio.crear_siguiente(
            fecha=date(2025, 1, 1), cuenta_pgc="705",
            importe_centimos=100, concepto="Test", creado_por="rubén",
        )
        d = repo_limpio.obtener(a.indice)
        assert d is not None
        assert d["hash"] == a.hash
        assert d["concepto"] == "Test"

    def test_obtener_inexistente(self, repo_limpio):
        assert repo_limpio.obtener(999_999) is None

    def test_por_cuenta(self, repo_limpio):
        repo_limpio.crear_siguiente(
            fecha=date(2025, 1, 1), cuenta_pgc="705",
            importe_centimos=100, concepto="Serv", creado_por="rubén",
        )
        repo_limpio.crear_siguiente(
            fecha=date(2025, 1, 2), cuenta_pgc="640",
            importe_centimos=200, concepto="Nóm", creado_por="rubén",
        )
        de_705 = repo_limpio.por_cuenta("705")
        assert len(de_705) >= 1
        assert all(r["cuenta_pgc"] == "705" for r in de_705)

    def test_por_fecha(self, repo_limpio):
        repo_limpio.crear_siguiente(
            fecha=date(2025, 6, 15), cuenta_pgc="705",
            importe_centimos=100, concepto="Jun", creado_por="rubén",
        )
        repo_limpio.crear_siguiente(
            fecha=date(2025, 7, 15), cuenta_pgc="705",
            importe_centimos=200, concepto="Jul", creado_por="rubén",
        )
        junio = repo_limpio.por_fecha(date(2025, 6, 1), date(2025, 6, 30))
        assert any(r["concepto"] == "Jun" for r in junio)
        assert not any(r["concepto"] == "Jul" for r in junio)


class TestVerificacion:
    def test_cadena_valida(self, repo_limpio):
        a0 = repo_limpio.crear_siguiente(
            fecha=date(2025, 1, 1), cuenta_pgc="705",
            importe_centimos=100, concepto="A", creado_por="rubén",
        )
        a1 = repo_limpio.crear_siguiente(
            fecha=date(2025, 1, 2), cuenta_pgc="705",
            importe_centimos=200, concepto="B", creado_por="rubén",
        )
        # Verificar solo el rango propio (no la historia completa,
        # que contiene cadenas artificiales de tests e2e)
        reporte = repo_limpio.verificar_cadena(desde=a0.indice, hasta=a1.indice)
        assert isinstance(reporte, ReporteCadena)
        assert reporte.cadena_valida, f"Roturas: {reporte.roturas}"
        assert reporte.total == 2

    def test_detecta_tampering_hash_previo(self, repo_limpio):
        a0 = repo_limpio.crear_siguiente(
            fecha=date(2025, 1, 1), cuenta_pgc="705",
            importe_centimos=100, concepto="A", creado_por="rubén",
        )
        a1 = repo_limpio.crear_siguiente(
            fecha=date(2025, 1, 2), cuenta_pgc="705",
            importe_centimos=200, concepto="B", creado_por="rubén",
        )
        with psycopg.connect(PG_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE acto_economico SET hash_previo = %s WHERE indice = %s",
                    ("0" * 64, a1.indice),
                )
            conn.commit()
        reporte = repo_limpio.verificar_cadena(
            desde=a0.indice, hasta=a1.indice,
        )
        assert not reporte.cadena_valida
        assert any(r["tipo"] == "rotura_cadena" for r in reporte.roturas)

    def test_detecta_tampering_concepto(self, repo_limpio):
        a = repo_limpio.crear_siguiente(
            fecha=date(2025, 1, 1), cuenta_pgc="705",
            importe_centimos=100, concepto="Original", creado_por="rubén",
        )
        with psycopg.connect(PG_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE acto_economico SET concepto = %s WHERE indice = %s",
                    ("Modificado", a.indice),
                )
            conn.commit()
        reporte = repo_limpio.verificar_cadena(
            desde=a.indice, hasta=a.indice,
        )
        assert not reporte.cadena_valida
        assert any(r["tipo"] == "huella_no_coincide" for r in reporte.roturas)


class TestVacio:
    def test_cadena_vacia_es_valida(self):
        repo = RepositorioActoEconomico()
        reporte = repo.verificar_cadena(desde=999_000, hasta=999_100)
        assert reporte.total == 0
        assert reporte.cadena_valida