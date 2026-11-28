# -*- coding: utf-8 -*-
"""Configuración común de pruebas: separa las que necesitan PostgreSQL real."""
from __future__ import annotations

import os

import pytest

os.environ.setdefault("CONTA_PG_URL", "postgresql://test:test@localhost:5432/test")

_MODULOS_CON_POSTGRES = frozenset({
    "tests/test_acto_economico.py",
    "tests/test_api.py",
    "tests/test_api_corpus.py",
    "tests/test_api_custodia.py",
    "tests/test_api_transiciones.py",
    "tests/test_auth.py",
    "tests/test_cadena_e2e.py",
    "tests/test_cli.py",
    "tests/test_cli_pd.py",
    "tests/test_cli_pd_verificar_reset.py",
    "tests/test_conftest.py",
    "tests/test_consolidacion.py",
    "tests/test_corpus_agregacion.py",
    "tests/test_corpus_forense.py",
    "tests/test_cuentas_anuales_oficiales.py",
    "tests/test_economico_contabilidad.py",
    "tests/test_custodia.py",
    "tests/test_frontend_corpus.py",
    "tests/test_justificacion_interna.py",
    "tests/test_libros.py",
    "tests/test_mapeo_abcd.py",
    "tests/test_multi_tenant.py",
    "tests/test_partida_doble.py",
    "tests/test_presentacion.py",
    "tests/test_reclasificacion.py",
    "tests/test_repositorio_acto.py",
    "tests/test_seed_corpus.py",
    "tests/test_seed_pgc.py",
    "tests/tests/test_backdating_cadena.py",
})


def pytest_collection_modifyitems(items):
    for item in items:
        ruta = item.path.relative_to(item.config.rootpath).as_posix()
        if ruta in _MODULOS_CON_POSTGRES:
            item.add_marker(pytest.mark.integration)
