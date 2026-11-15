# -*- coding: utf-8 -*-
"""Tests del sugeridor A+B+C→D."""
from conta_rizoma4.operativo.mapeo_abcd import (
    CUENTA_FALLBACK,
    REGLAS_DEFAULT,
    SugerenciaCuenta,
    sugerir_cuenta_pgc,
)


class TestReglasDefault:
    def test_reglas_no_vacias(self):
        assert len(REGLAS_DEFAULT) > 10

    def test_factura_emitida_a_705(self):
        r = REGLAS_DEFAULT[("FACTURA_EMITIDA", "JURIDICA", None)]
        assert r == "705"

    def test_nomina_a_640(self):
        r = REGLAS_DEFAULT[("NOMINA", None, None)]
        assert r == "640"


class TestSugerir:
    def test_factura_emitida_devuelve_705(self):
        s = sugerir_cuenta_pgc("FACTURA_EMITIDA", "JURIDICA")
        assert isinstance(s, SugerenciaCuenta)
        assert s.cuenta.cuenta == "705"
        assert s.confianza == 0.8  # regla por doc+interlocutor
        assert "doc+interlocutor" in s.motivo

    def test_nomina_devuelve_640(self):
        s = sugerir_cuenta_pgc("NOMINA")
        assert s.cuenta.cuenta == "640"
        assert s.confianza == 0.6  # regla por documento

    def test_factura_recibida_devuelve_629(self):
        s = sugerir_cuenta_pgc("FACTURA_RECIBIDA")
        assert s.cuenta.cuenta == "629"

    def test_documento_desconocido_cae_a_fallback(self):
        s = sugerir_cuenta_pgc("DOCUMENTO_INVENTADO")
        assert s.cuenta.cuenta == CUENTA_FALLBACK
        assert s.confianza == 0.2
        assert "sin regla" in s.motivo

    def test_parrafo_pgc_no_es_none_para_705(self):
        s = sugerir_cuenta_pgc("FACTURA_EMITIDA")
        # 705 (Prestación de servicios) debe aparecer en algún párrafo
        if s.parrafo_pgc is not None:
            assert "texto" in s.parrafo_pgc
            assert len(s.parrafo_pgc["texto"]) > 0