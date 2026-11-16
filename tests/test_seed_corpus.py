# -*- coding: utf-8 -*-
"""Test del dataset sintético del corpus forense."""
import psycopg
import pytest

from conta_rizoma4.corpus_forense.agregacion import agregar_corpus
from conta_rizoma4.custodia.repositorios import PG_URL


def _limpiar():
    """Borra TODOS los datos de test (TEST_% y SYN_%)."""
    with psycopg.connect(PG_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM danos WHERE expediente_id LIKE 'TEST_%' OR expediente_id LIKE 'SYN_%'")
            cur.execute("DELETE FROM flujos WHERE expediente_id LIKE 'TEST_%' OR expediente_id LIKE 'SYN_%'")
            cur.execute("DELETE FROM expedientes WHERE expediente_id LIKE 'TEST_%' OR expediente_id LIKE 'SYN_%'")
            cur.execute("DELETE FROM sujetos WHERE sujeto_id LIKE 'TEST_%' OR sujeto_id LIKE 'SYN_%'")
        conn.commit()


@pytest.fixture
def dataset():
    _limpiar()
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from scripts.seed_corpus_forense import main
    main()
    yield
    _limpiar()


class TestSeedCorpus:
    def test_6_expedientes(self, dataset):
        r = agregar_corpus()
        assert r["totales"]["n_expedientes"] == 6

    def test_3_u1(self, dataset):
        r = agregar_corpus(universo="U1")
        assert r["totales"]["n_expedientes"] == 3

    def test_distribucion(self, dataset):
        r = agregar_corpus()
        universos = {u["universo"]: u["n"] for u in r["por_universo"]}
        # Distribución real del seed:
        # U1: 3 (XYZ, ABC, Rubén)
        # U2: 0 (DEF es U3, porque 15% < 20%)
        # U3: 2 (DEF, GHI)
        # no_victima: 1 (Juan)
        assert universos.get("U1") == 3
        assert universos.get("U3") == 2
        assert universos.get("no_victima") == 1
