# -*- coding: utf-8 -*-
"""Tests de partida doble."""
from datetime import date

import psycopg
import pytest

from conta_rizoma4.partida_doble import (
    Asiento, Linea, PartidaDobleError,
    crear_asiento, guardar_asiento,
    RepositorioAsiento,
)
from conta_rizoma4.partida_doble.persistencia import PG_URL
from test_helpers_db import limpiar_asiento_prueba


class TestLinea:
    def test_debe_ok(self):
        l = Linea("430", debe_centimos=1000)
        assert l.debe_centimos == 1000 and l.haber_centimos == 0
        assert l.parrafo_pgc_id is None
        assert "PGC §" not in str(l)

    def test_parrafo_pgc_explicito_se_conserva(self):
        l = Linea("430", debe_centimos=1000, parrafo_pgc_id=42)
        assert l.parrafo_pgc_id == 42
        assert "PGC §42" in str(l)

    def test_haber_ok(self):
        l = Linea("705", haber_centimos=1000)
        assert l.haber_centimos == 1000

    def test_ambos_falla(self):
        with pytest.raises(PartidaDobleError):
            Linea("430", debe_centimos=100, haber_centimos=100)

    def test_cero_falla(self):
        with pytest.raises(PartidaDobleError):
            Linea("430", debe_centimos=0, haber_centimos=0)

    def test_negativa_falla(self):
        with pytest.raises(PartidaDobleError):
            Linea("430", debe_centimos=-1)


class TestAsiento:
    def test_cuadra(self):
        a = crear_asiento(
            indice=0, fecha=date(2025, 1, 1), concepto="Factura",
            lineas=[
                Linea("430", debe_centimos=121_000),
                Linea("705", haber_centimos=100_000),
                Linea("477", haber_centimos=21_000),
            ],
        )
        assert isinstance(a, Asiento)
        assert a.cuadra
        assert a.total_debe == a.total_haber == 121_000

    def test_descuadra(self):
        with pytest.raises(PartidaDobleError, match="descuadre"):
            crear_asiento(
                indice=0, fecha=date(2025, 1, 1), concepto="X",
                lineas=[
                    Linea("430", debe_centimos=1000),
                    Linea("705", haber_centimos=900),
                ],
            )

    def test_una_linea(self):
        with pytest.raises(PartidaDobleError, match="al menos 2"):
            crear_asiento(
                indice=0, fecha=date(2025, 1, 1), concepto="X",
                lineas=[Linea("430", debe_centimos=1000)],
            )

    def test_hash_determinista(self):
        kw = dict(
            indice=5, fecha=date(2025, 1, 1), concepto="X",
            lineas=[
                Linea("430", debe_centimos=100),
                Linea("705", haber_centimos=100),
            ],
        )
        assert crear_asiento(**kw).hash == crear_asiento(**kw).hash


class TestPersistencia:
    @pytest.fixture(autouse=True)
    def cleanup(self):
        limpiar_asiento_prueba(9500); limpiar_asiento_prueba(9501)
        yield
        limpiar_asiento_prueba(9500); limpiar_asiento_prueba(9501)

    def test_guardar_y_leer(self):
        a = crear_asiento(
            indice=9500, fecha=date(2025, 6, 15), concepto="Test",
            lineas=[
                Linea("430", debe_centimos=121_000),
                Linea("705", haber_centimos=100_000),
                Linea("477", haber_centimos=21_000),
            ],
        )
        guardar_asiento(a)
        d = RepositorioAsiento('default').obtener(9500)
        assert d is not None
        assert d["concepto"] == "Test"
        assert len(d["lineas"]) == 3

    def test_cuadre_en_bd(self):
        a = crear_asiento(
            indice=9501, fecha=date(2025, 6, 15), concepto="Cuadre",
            lineas=[
                Linea("430", debe_centimos=121_000),
                Linea("705", haber_centimos=100_000),
                Linea("477", haber_centimos=21_000),
            ],
        )
        guardar_asiento(a)
        with psycopg.connect(PG_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT total_debe, total_haber, descuadre "
                    "FROM v_asiento_cuadre WHERE asiento_indice = 9501"
                )
                debe, haber, desc = cur.fetchone()
        assert debe == haber == 121_000 and desc == 0


class TestRepositorio:
    @pytest.fixture(autouse=True)
    def cleanup(self):
        for i in (9600, 9601):
            limpiar_asiento_prueba(i)
        yield
        for i in (9600, 9601):
            limpiar_asiento_prueba(i)

    def test_cadena_encadenada(self):
        a0 = crear_asiento(
            indice=9600, fecha=date(2025, 1, 1), concepto="A",
            lineas=[Linea("430", debe_centimos=100),
                    Linea("705", haber_centimos=100)],
        )
        a1 = crear_asiento(
            indice=9601, fecha=date(2025, 1, 2), concepto="B",
            lineas=[Linea("430", debe_centimos=200),
                    Linea("705", haber_centimos=200)],
            hash_previo=a0.hash,
        )
        guardar_asiento(a0); guardar_asiento(a1)
        rep = RepositorioAsiento('default').verificar_cadena(desde=9600, hasta=9601)
        assert rep.cadena_valida, f"Roturas: {rep.roturas}"
        assert rep.total == 2


class TestFiscal:
    @pytest.fixture(autouse=True)
    def cleanup(self):
        limpiar_asiento_prueba(9700)
        yield
        limpiar_asiento_prueba(9700)

    def test_liquidacion_iva_303(self):
        # 477=2100 D, 472=1500 H, 4750=600 H → cuadra
        a = crear_asiento(
            indice=9700, fecha=date(2025, 3, 31),
            concepto="Liquidación IVA T1 2025 (modelo 303)",
            lineas=[
                Linea("477", debe_centimos=210_000),
                Linea("472", haber_centimos=150_000),
                Linea("4750", haber_centimos=60_000),
            ],
        )
        assert a.cuadra
        guardar_asiento(a)
        d = RepositorioAsiento('default').obtener(9700)
        assert len(d["lineas"]) == 3
