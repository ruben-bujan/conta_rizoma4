# -*- coding: utf-8 -*-
"""Tests de las primitivas hash chain."""
from conta_rizoma4.operativo.asiento import (
    GENESIS, calcular_hash, calcular_huella,
)


class TestHash:
    def test_genesis_es_64_ceros(self):
        assert GENESIS == "0" * 64
        assert len(GENESIS) == 64

    def test_huella_es_sha256(self):
        h = calcular_huella({"a": 1, "b": 2})
        assert len(h) == 64
        assert h == calcular_huella({"b": 2, "a": 1})  # orden no importa

    def test_huella_cambia_con_contenido(self):
        h1 = calcular_huella({"a": 1})
        h2 = calcular_huella({"a": 2})
        assert h1 != h2

    def test_hash_encadenado(self):
        h = calcular_hash("a" * 64, GENESIS, 0)
        assert len(h) == 64
        # Mismo input, mismo hash
        assert h == calcular_hash("a" * 64, GENESIS, 0)
        # Cambio de indice → distinto hash
        assert h != calcular_hash("a" * 64, GENESIS, 1)

    def test_hash_previo_vacio_falla(self):
        import pytest
        with pytest.raises(ValueError):
            calcular_hash("a" * 64, "", 0)

    def test_indice_negativo_falla(self):
        import pytest
        with pytest.raises(ValueError):
            calcular_hash("a" * 64, GENESIS, -1)