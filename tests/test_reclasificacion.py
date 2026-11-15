# -*- coding: utf-8 -*-
"""Tests de la reclasificación del devengo.

Flujo: JustificacionInterna (4308) → ActoEconomico (430, contrapartida 4308).
"""
from __future__ import annotations

from datetime import date

import psycopg
import pytest

from conta_rizoma4.operativo.acto_economico import PG_URL
from conta_rizoma4.operativo.justificacion_interna import (
    crear_justificacion_interna,
    guardar_justificacion_interna,
)
from conta_rizoma4.operativo.reclasificacion import (
    ReclasificacionError,
    justificaciones_pendientes,
    justificaciones_reclasificadas,
    reclasificar_justificacion,
)
from conta_rizoma4.operativo.repositorio_acto import RepositorioActoEconomico


@pytest.fixture
def entorno_limpio():
    """Limpia actos y justificaciones por encima del índice inicial."""
    repo = RepositorioActoEconomico()
    idx_acto_inicial = repo.ultimo_indice()

    with psycopg.connect(PG_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COALESCE(MAX(indice), -1) FROM justificacion_interna")
            idx_just_inicial = cur.fetchone()[0]
        conn.commit()

    def _limpia():
        with psycopg.connect(PG_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM acto_economico WHERE indice > %s",
                    (idx_acto_inicial,),
                )
                cur.execute(
                    "DELETE FROM justificacion_interna WHERE indice > %s",
                    (idx_just_inicial,),
                )
            conn.commit()

    _limpia()
    yield repo
    _limpia()


def _crear_justificacion(idx: int, importe: int = 50_000) -> "JustificacionInterna":
    j = crear_justificacion_interna(
        indice=idx, fecha=date(2025, 3, 1),
        cuenta_pgc="4308", importe_centimos=importe,
        concepto="Obra ejecutada", creado_por="rubén",
        obra_ref="OBRA-2025-01",
    )
    guardar_justificacion_interna(j)
    return j


class TestReclasificar:
    def test_reclasificacion_basica(self, entorno_limpio):
        j = _crear_justificacion(9700)
        acto = reclasificar_justificacion(
            j, creado_por="rubén", repo=entorno_limpio,
        )
        assert acto.cuenta_pgc == "430"
        assert acto.cuenta_contrapartida == "4308"
        assert acto.justificacion_indice == 9700
        assert acto.importe_centimos == 50_000
        # Persistido
        d = entorno_limpio.obtener(acto.indice)
        assert d is not None
        assert d["justificacion_indice"] == 9700
        assert d["cuenta_contrapartida"] == "4308"

    def test_cuenta_destino_personalizada(self, entorno_limpio):
        j = _crear_justificacion(9701)
        acto = reclasificar_justificacion(
            j, creado_por="rubén", cuenta_destino="431",
            repo=entorno_limpio,
        )
        assert acto.cuenta_pgc == "431"

    def test_no_reclasificar_dos_veces(self, entorno_limpio):
        j = _crear_justificacion(9702)
        reclasificar_justificacion(j, creado_por="rubén", repo=entorno_limpio)
        with pytest.raises(ReclasificacionError, match="ya reclasificada"):
            reclasificar_justificacion(j, creado_por="rubén", repo=entorno_limpio)

    def test_cuenta_destino_igual_a_origen_falla(self, entorno_limpio):
        j = _crear_justificacion(9703)
        with pytest.raises(ReclasificacionError, match="sería un no-op"):
            reclasificar_justificacion(
                j, creado_por="rubén", cuenta_destino="4308",
                repo=entorno_limpio,
            )

    def test_importe_cero_falla(self, entorno_limpio):
        j = _crear_justificacion(9704, importe=0)
        with pytest.raises(ReclasificacionError, match="importe_centimos == 0"):
            reclasificar_justificacion(j, creado_por="rubén", repo=entorno_limpio)


class TestConsultas:
    def test_pendientes_antes_de_reclasificar(self, entorno_limpio):
        j = _crear_justificacion(9710)
        pend = justificaciones_pendientes()
        assert any(p["indice"] == 9710 for p in pend)

    def test_pendientes_despues_de_reclasificar(self, entorno_limpio):
        j = _crear_justificacion(9711)
        reclasificar_justificacion(j, creado_por="rubén", repo=entorno_limpio)
        pend = justificaciones_pendientes()
        assert not any(p["indice"] == 9711 for p in pend)

    def test_reclasificadas_incluye_la_resuelta(self, entorno_limpio):
        j = _crear_justificacion(9712)
        acto = reclasificar_justificacion(
            j, creado_por="rubén", repo=entorno_limpio,
        )
        recl = justificaciones_reclasificadas()
        coincidencia = [r for r in recl if r["justificacion_indice"] == 9712]
        assert len(coincidencia) == 1
        assert coincidencia[0]["acto_indice"] == acto.indice
        assert coincidencia[0]["cuenta_destino"] == "430"


class TestVerificacionDeCadena:
    def test_cadena_incluye_justificacion_indice(self, entorno_limpio):
        j = _crear_justificacion(9720)
        acto = reclasificar_justificacion(
            j, creado_por="rubén", repo=entorno_limpio,
        )
        rep = entorno_limpio.verificar_cadena(
            desde=acto.indice, hasta=acto.indice,
        )
        assert rep.cadena_valida, f"Roturas: {rep.roturas}"

    def test_tampering_de_justificacion_indice_detectado(self, entorno_limpio):
        j = _crear_justificacion(9721)
        acto = reclasificar_justificacion(
            j, creado_por="rubén", repo=entorno_limpio,
        )
        # Manipular el enlace
        with psycopg.connect(PG_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE acto_economico SET justificacion_indice = 9999 "
                    "WHERE indice = %s",
                    (acto.indice,),
                )
            conn.commit()
        rep = entorno_limpio.verificar_cadena(
            desde=acto.indice, hasta=acto.indice,
        )
        assert not rep.cadena_valida
        assert any(r["tipo"] == "huella_no_coincide" for r in rep.roturas)

class TestMetadatos:
    def test_reclasificacion_acepta_metadatos(self, entorno_limpio):
        j = _crear_justificacion(9730)
        acto = reclasificar_justificacion(
            j, creado_por="rubén", repo=entorno_limpio,
            metadatos={"fuente": "test", "lote": 42},
        )
        d = entorno_limpio.obtener(acto.indice)
        assert d["metadatos"]["fuente"] == "test"
        assert d["metadatos"]["lote"] == 42
