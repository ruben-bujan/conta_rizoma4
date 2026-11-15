# -*- coding: utf-8 -*-
"""Tests de la config de empresas (carga + validación + tipos de cambio)."""
from datetime import date
from pathlib import Path

import pytest
import yaml

from conta_rizoma4.config import (
    ConfigError, cargar_config, get_empresa, get_config,
    obtener_tipo_cambio, recargar_config, TiposCambioError,
)


class TestCargarConfig:
    def test_default_carga(self):
        cfg = get_config()
        assert cfg.version == 1
        assert cfg.moneda_grupo == "EUR"
        assert "default" in cfg.empresas

    def test_empresa_obligatoria(self):
        with pytest.raises(ConfigError, match="no está en config"):
            get_empresa("NO_EXISTE")

    def test_empresa_default(self):
        e = get_empresa("default")
        assert e.moneda_funcional == "EUR"
        assert e.marco_contable == "PGC_ES"
        assert e.participacion_matriz == 100.0

    def test_config_invalida_falla(self, tmp_path):
        # YAML con empresa duplicada
        yml = tmp_path / "mal.yaml"
        yml.write_text(yaml.dump({
            "version": 1,
            "moneda_grupo": "EUR",
            "marco_contable_default": "PGC_ES",
            "marcos_contables": {"PGC_ES": {"pais": "ES"}},
            "empresas": [
                {"empresa_id": "A", "moneda_funcional": "EUR",
                 "marco_contable": "PGC_ES"},
                {"empresa_id": "A", "moneda_funcional": "EUR",
                 "marco_contable": "PGC_ES"},
            ],
        }))
        with pytest.raises(ConfigError, match="duplicado"):
            cargar_config(yml)

    def test_moneda_invalida_falla(self, tmp_path):
        yml = tmp_path / "mal.yaml"
        yml.write_text(yaml.dump({
            "version": 1,
            "moneda_grupo": "EUR",
            "marco_contable_default": "PGC_ES",
            "marcos_contables": {"PGC_ES": {"pais": "ES"}},
            "empresas": [
                {"empresa_id": "A", "moneda_funcional": "XYZ",
                 "marco_contable": "PGC_ES"},
            ],
        }))
        with pytest.raises(ConfigError, match="no válida"):
            cargar_config(yml)

    def test_participacion_fuera_rango_falla(self, tmp_path):
        yml = tmp_path / "mal.yaml"
        yml.write_text(yaml.dump({
            "version": 1,
            "moneda_grupo": "EUR",
            "marco_contable_default": "PGC_ES",
            "marcos_contables": {"PGC_ES": {"pais": "ES"}},
            "empresas": [
                {"empresa_id": "A", "moneda_funcional": "EUR",
                 "marco_contable": "PGC_ES", "participacion_matriz": 150.0},
            ],
        }))
        with pytest.raises(ConfigError, match="participacion_matriz"):
            cargar_config(yml)


class TestTiposCambio:
    def test_par_invalido(self):
        with pytest.raises(TiposCambioError, match="par inválido"):
            obtener_tipo_cambio(date.today(), "USD")

    def test_manual_tiene_prioridad(self):
        # USD_EUR 2025-12-31 está en el YAML manual
        tasa = obtener_tipo_cambio(date(2025, 12, 31), "USD_EUR")
        assert tasa == 0.92

    def test_eur_eur_es_1(self):
        # EUR_EUR debe ser 1 aunque no esté manual ni en caché.
        # (Solo si el BCE está accesible o si hay caché de hoy.)
        # Si no hay red, skip.
        try:
            tasa = obtener_tipo_cambio(date.today(), "EUR_EUR")
            assert tasa == 1.0
        except TiposCambioError:
            pytest.skip("Sin red ni caché")
