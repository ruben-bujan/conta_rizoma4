# -*- coding: utf-8 -*-
"""Tests de pd-verificar y pd-reset."""
import pytest
import psycopg

from conta_rizoma4.cli import main
from conta_rizoma4.partida_doble.persistencia import PG_URL


@pytest.fixture(autouse=True)
def cadena_vacia():
    with psycopg.connect(PG_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM linea_asiento WHERE empresa_id = 'default'")
            cur.execute("DELETE FROM asiento_contable WHERE empresa_id = 'default'")
        conn.commit()


class TestVerificar:
    def test_verificar_cadena_vacia(self, capsys):
        rc = main(["pd-verificar"])
        out = capsys.readouterr().out
        # rc es 0 si vacío (cadena_valida=True cuando total=0)
        assert rc == 0
        assert "Cadena VÁLIDA" in out or "Asientos verificados: 0" in out


class TestReset:
    def test_reset_sin_yes_pide_confirmacion(self, capsys):
        rc = main(["pd-reset"])
        out = capsys.readouterr().out
        assert rc == 2
        assert "deshabilitado" in out

    def test_reset_con_yes_tampoco_conecta_a_la_base(self, capsys, monkeypatch):
        monkeypatch.setattr(
            psycopg, "connect",
            lambda *a, **kw: (_ for _ in ()).throw(AssertionError("no debe conectar")),
        )
        rc = main(["pd-reset", "--yes"])
        out = capsys.readouterr().out
        assert rc == 2
        assert "deshabilitado" in out
