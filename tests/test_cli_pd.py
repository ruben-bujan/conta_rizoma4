# -*- coding: utf-8 -*-
"""Tests del CLI de partida doble."""
import pytest

from conta_rizoma4.cli import main
from conta_rizoma4.partida_doble import RepositorioAsiento
from test_helpers_db import limpiar_asiento_prueba


@pytest.fixture
def limpio():
    for i in (7000, 7001, 7002):
        limpiar_asiento_prueba(i)
    yield
    for i in (7000, 7001, 7002):
        limpiar_asiento_prueba(i)


class TestCatalogo:
    def test_listar(self, capsys):
        rc = main(["pd-acto", "listar"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "115" in out
        assert "A_FACT_EMIT_SERV_NAC_SIN_RET" in out

    def test_listar_por_grupo(self, capsys):
        rc = main(["pd-acto", "listar", "--grupo", "facturacion"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "A_FACT_EMIT_SERV_NAC_SIN_RET" in out


class TestCrear:
    def test_crear_factura(self, capsys, limpio):
        repo = RepositorioAsiento('default')
        indice_antes = repo.ultimo_indice()
        rc = main([
            "pd-acto", "crear", "A_FACT_EMIT_SERV_NAC_SIN_RET",
            "--json", '{"fecha":"2025-04-15","base_centimos":100000,'
                     '"iva_pct":21,"cliente_nif":"B12345678","concepto":"Test"}',
        ])
        out = capsys.readouterr().out
        assert rc == 0
        assert "Asiento #" in out
        indice = indice_antes + 1
        d = repo.obtener(indice)
        assert d is not None
        assert len(d["lineas"]) == 3
        # Limpiar
        limpiar_asiento_prueba(indice)

    def test_crear_codigo_invalido(self, capsys):
        rc = main([
            "pd-acto", "crear", "A_NO_EXISTE",
            "--json", '{"fecha":"2025-04-15"}',
        ])
        err = capsys.readouterr().err
        assert rc == 1
        assert "Acto desconocido" in err

    def test_crear_json_invalido(self):
        with pytest.raises(SystemExit):
            main([
                "pd-acto", "crear", "A_FACT_EMIT_SERV_NAC_SIN_RET",
                "--json", 'no es json',
            ])


class TestConsultas:
    def test_diario(self, capsys):
        rc = main(["pd-diario"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "Total debe" in out or "diario vacío" in out

    def test_pyg(self, capsys):
        rc = main(["pd-pyg"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "RESULTADO" in out

    def test_situacion(self, capsys):
        rc = main(["pd-situacion"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "ACTIVO" in out
        assert "PASIVO" in out

    def test_balance(self, capsys):
        rc = main(["pd-balance"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "TOTAL" in out

    def test_mayor(self, capsys):
        rc = main(["pd-mayor"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "cuenta" in out or "(cuenta" in out
