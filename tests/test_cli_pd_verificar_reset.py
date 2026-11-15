# -*- coding: utf-8 -*-
"""Tests de pd-verificar y pd-reset."""
import pytest

from conta_rizoma4.cli import main
from conta_rizoma4.partida_doble import borrar_asiento, RepositorioAsiento


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
        assert rc == 1
        assert "ADVERTENCIA" in out
        assert "pd-reset --yes" in out

    def test_reset_con_yes_limpia(self, capsys):
        repo = RepositorioAsiento('default')
        # Crear un asiento si no hay ninguno
        from datetime import date
        from conta_rizoma4.actos.facturacion import fact_emit_serv_nac_sin_ret
        from conta_rizoma4.operativo.asiento import GENESIS
        from conta_rizoma4.partida_doble import guardar_asiento

        indice = repo.ultimo_indice() + 1
        a = fact_emit_serv_nac_sin_ret(
            indice=indice, hash_previo=GENESIS, fecha=date(2025, 1, 1),
            base_centimos=100_000, iva_pct=21,
            cliente_nif="B1", concepto="Test reset",
        )
        guardar_asiento(a)
        assert repo.contar() >= 1

        # Reset
        rc = main(["pd-reset", "--yes"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "limpia" in out
        assert repo.contar() == 0
