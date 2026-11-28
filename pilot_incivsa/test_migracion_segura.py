"""Contratos puros del importador seguro; no conectan con PostgreSQL."""
from datetime import date

from pilot_incivsa.constructor_memoria import GrupoOrigen
from scripts.incorporar_incivsa import (
    GENESIS, PARSER_VERSION, _clave_grupo, _contenido_hash, _lote_id,
)


def test_clave_origen_incluye_codigo_y_fecha():
    primero = GrupoOrigen("42", "01/02/25", (), "NO_DETERMINADO_FECHA")
    segundo = GrupoOrigen("42", "01/03/25", (), "NO_DETERMINADO_FECHA")

    assert _clave_grupo(primero) != _clave_grupo(segundo)
    assert _clave_grupo(primero) == _clave_grupo(primero)


def test_lote_es_determinista_por_fuente_y_parser():
    assert _lote_id("a" * 64) == _lote_id("a" * 64)
    assert _lote_id("a" * 64) != _lote_id("b" * 64)
    assert PARSER_VERSION


def test_payload_hash_usa_fecha_contable_sin_hora():
    contenido, lineas = _contenido_hash(
        fecha=date(2025, 1, 2), concepto="fixture sintético", lineas=(),
        metadatos={"estado_epistemologico": "NO_DETERMINADO"},
    )
    assert contenido["fecha"] == "2025-01-02"
    assert lineas == []
    assert len(GENESIS) == 64
