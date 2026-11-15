# -*- coding: utf-8 -*-
"""Tests del CLI. Llaman a main(argv) directamente, sin subprocess."""
from __future__ import annotations

import psycopg
import pytest

from conta_rizoma4.cli import main
from conta_rizoma4.operativo.acto_economico import PG_URL


@pytest.fixture
def entorno_limpio():
    """Limpia actos y justificaciones por encima del índice inicial."""
    with psycopg.connect(PG_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COALESCE(MAX(indice), -1) FROM acto_economico")
            idx_acto = cur.fetchone()[0]
            cur.execute("SELECT COALESCE(MAX(indice), -1) FROM justificacion_interna")
            idx_just = cur.fetchone()[0]
        conn.commit()

    def _limpia():
        with psycopg.connect(PG_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM acto_economico WHERE indice > %s",
                    (idx_acto,),
                )
                cur.execute(
                    "DELETE FROM justificacion_interna WHERE indice > %s",
                    (idx_just,),
                )
            conn.commit()

    _limpia()
    yield
    _limpia()


class TestSugerir:
    def test_sugerir_factura_emitida(self, capsys):
        rc = main(["sugerir", "--doc", "FACTURA_EMITIDA", "--int", "JURIDICA"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "705" in out
        assert "Confianza:       0.80" in out

    def test_sugerir_documento_desconocido(self, capsys):
        rc = main(["sugerir", "--doc", "INVENTADO"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "555" in out
        assert "0.20" in out


class TestCrear:
    def test_crear_acto(self, capsys, entorno_limpio):
        rc = main([
            "crear", "--cuenta", "705", "--importe", "1210.00",
            "--concepto", "Factura test", "--por", "rubén",
        ])
        out = capsys.readouterr().out
        assert rc == 0
        assert "ActoEconomico #" in out
        assert "1210.00 EUR" in out

    def test_importe_invalido(self, capsys):
        with pytest.raises(SystemExit) as exc:
            main([
                "crear", "--cuenta", "705", "--importe", "abc",
                "--concepto", "X", "--por", "rubén",
            ])
        assert exc.value.code == 2


class TestFlujoCompleto:
    def test_justificar_reclasificar_listar_verificar(
        self, capsys, entorno_limpio,
    ):
        # 1. Justificar
        rc = main([
            "justificar", "--cuenta", "4308", "--importe", "1210.00",
            "--concepto", "Obra test", "--obra", "OBRA-01", "--por", "rubén",
        ])
        out = capsys.readouterr().out
        assert rc == 0
        assert "JustificacionInterna #" in out
        idx_just = int(out.split("JustificacionInterna #")[1].split()[0])

        # 2. Reclasificar
        rc = main([
            "reclasificar", "--justificacion", str(idx_just), "--por", "rubén",
        ])
        out = capsys.readouterr().out
        assert rc == 0
        assert "reclasifica" in out
        # Extraer índice del acto recién creado: "ActoEconomico #9117 creado"
        idx_acto = int(out.split("ActoEconomico #")[1].split()[0])

        # 3. Listar solo los actos de la cuenta 430 (Clientes)
        rc = main(["listar", "--cuenta", "430", "--limite", "10"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "430" in out
        assert "Total:" in out

        # 4. Verificar SOLO el rango del acto creado.
        # (verificar sin rango recorre la historia completa, que contiene
        # cadenas artificiales de otros tests con hash_previo=GENESIS)
        rc = main([
            "verificar", "--desde", str(idx_acto), "--hasta", str(idx_acto),
        ])
        out = capsys.readouterr().out
        assert rc == 0
        assert "Cadena VÁLIDA" in out


class TestPendientes:
    def test_sin_pendientes(self, capsys, entorno_limpio):
        rc = main(["pendientes"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "pendiente" in out.lower() or "ninguna" in out.lower()


class TestVer:
    def test_ver_inexistente(self, capsys):
        rc = main(["ver", "--indice", "999999"])
        err = capsys.readouterr().err
        assert rc == 1
        assert "no encontrado" in err
