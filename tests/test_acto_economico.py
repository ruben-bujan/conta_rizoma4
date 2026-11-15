# -*- coding: utf-8 -*-
"""Tests del ActoEconomico: hash chain, cadena de mando, persistencia."""
from datetime import date

import psycopg
import pytest

from conta_rizoma4.operativo.asiento import GENESIS
from conta_rizoma4.operativo.acto_economico import (
    PG_URL,
    ActoEconomico,
    crear_acto_economico,
    guardar_acto_economico,
    leer_ultimo_acto,
)


class TestCrear:
    def test_crear_acto_basico(self):
        a = crear_acto_economico(
            indice=0, fecha=date(2025, 1, 15),
            cuenta_pgc="705", importe_centimos=121_000,
            concepto="Factura 2025-001", creado_por="rubén",
        )
        assert isinstance(a, ActoEconomico)
        assert a.indice == 0
        assert a.hash_previo == GENESIS
        assert len(a.hash) == 64
        assert len(a.huella_contenido) == 64

    def test_importe_debe_ser_int(self):
        with pytest.raises(TypeError):
            crear_acto_economico(
                indice=0, fecha=date(2025, 1, 1),
                cuenta_pgc="705", importe_centimos=12.10,
                concepto="X", creado_por="rubén",
            )

    def test_creado_por_obligatorio(self):
        with pytest.raises(ValueError):
            crear_acto_economico(
                indice=0, fecha=date(2025, 1, 1),
                cuenta_pgc="705", importe_centimos=100,
                concepto="X", creado_por="",
            )

    def test_dos_actos_iguales_mismo_hash(self):
        kw = dict(
            indice=5, fecha=date(2025, 1, 15),
            cuenta_pgc="705", importe_centimos=121_000,
            concepto="Factura 2025-001", creado_por="rubén",
        )
        a1 = crear_acto_economico(**kw)
        a2 = crear_acto_economico(**kw)
        assert a1.hash == a2.hash
        assert a1.huella_contenido == a2.huella_contenido


class TestCadena:
    def test_tres_actos_encadenados(self):
        a0 = crear_acto_economico(
            indice=0, fecha=date(2025, 1, 1),
            cuenta_pgc="705", importe_centimos=100,
            concepto="A", creado_por="rubén",
        )
        a1 = crear_acto_economico(
            indice=1, fecha=date(2025, 1, 2),
            cuenta_pgc="705", importe_centimos=200,
            concepto="B", creado_por="rubén",
            hash_previo=a0.hash,
        )
        a2 = crear_acto_economico(
            indice=2, fecha=date(2025, 1, 3),
            cuenta_pgc="705", importe_centimos=300,
            concepto="C", creado_por="rubén",
            hash_previo=a1.hash,
        )
        assert a0.hash_previo == GENESIS
        assert a1.hash_previo == a0.hash
        assert a2.hash_previo == a1.hash
        assert a0.hash != a1.hash != a2.hash


class TestPersistencia:
    def test_guardar_y_leer(self):
        # Limpiar el índice del test antes y después
        with psycopg.connect(PG_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM acto_economico WHERE indice = 9000")
            conn.commit()

        a = crear_acto_economico(
            indice=9000, fecha=date(2025, 6, 15),
            cuenta_pgc="705", importe_centimos=121_000,
            concepto="Test persistencia", creado_por="rubén",
        )
        guardar_acto_economico(a)
        ultimo = leer_ultimo_acto()
        assert ultimo is not None
        assert ultimo["indice"] >= 9000

        # Limpiar
        with psycopg.connect(PG_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM acto_economico WHERE indice = 9000")
            conn.commit()
