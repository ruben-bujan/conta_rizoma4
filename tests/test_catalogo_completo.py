# -*- coding: utf-8 -*-
"""Smoke test: todos los actos del catálogo existen y son invocables.

No es golden test (eso lo tienen los actos del 7-11).
Verifica que:
  - El catálogo tiene N actos.
  - Cada código está en un grupo.
  - Cada acto es invocable (la función existe y es callable).
"""
from conta_rizoma4.actos.catalogo import (
    CATALOGO, listar_grupos, listar_por_grupo, obtener, contar,
)


class TestCatalogoCompleto:
    def test_contar_cobertura_completa(self):
        # 51 (ciclos 7-11) + 51 (avanzados) + 13 (especiales) = 115
        # La taxonomía original eran ~100 actos. 115 es cobertura completa.
        n = contar()
        assert n >= 110, f"Esperados >=110 actos (100% taxonomía), hay {n}"

    def test_grupos(self):
        grupos = listar_grupos()
        assert len(grupos) >= 14
        esperados = {
            "facturacion", "facturacion_avanzada",
            "fiscal", "fiscal_avanzado",
            "cierre",
            "inmovilizado", "inmovilizado_avanzado",
            "existencias", "existencias_avanzado",
            "societarias", "societarias_avanzado",
            "ajustes", "ajustes_avanzado",
            "operaciones_especiales",
        }
        for g in esperados:
            assert g in grupos, f"Falta grupo {g}"

    def test_todos_invocables(self):
        for codigo, (grupo, fn) in CATALOGO.items():
            assert callable(fn), f"{codigo} no es callable"
            assert grupo, f"{codigo} sin grupo"

    def test_obtener_inexistente_falla(self):
        import pytest
        with pytest.raises(ValueError, match="Acto desconocido"):
            obtener("A_NO_EXISTE")

    def test_codigos_unicos(self):
        # El dict ya garantiza unicidad, pero verificamos por sanity
        codigos = list(CATALOGO.keys())
        assert len(codigos) == len(set(codigos))

    def test_codigos_tienen_prefijo_A_(self):
        for codigo in CATALOGO.keys():
            assert codigo.startswith("A_"), f"{codigo} no empieza por A_"


class TestSmokeCrear:
    """Verifica que crear_acto produce un asiento que cuadra."""

    def test_factura_basica(self):
        from datetime import date
        from conta_rizoma4.operaciones import crear_acto_por_codigo
        from conta_rizoma4.operativo.asiento import GENESIS
        a = crear_acto_por_codigo(
            "A_FACT_EMIT_SERV_NAC_SIN_RET",
            indice=0, hash_previo=GENESIS, fecha=date(2025, 1, 1),
            base_centimos=100_000, iva_pct=21,
            cliente_nif="B1", concepto="Test",
        )
        assert a.cuadra

    def test_fusion(self):
        from datetime import date
        from conta_rizoma4.operaciones import crear_acto_por_codigo
        from conta_rizoma4.operativo.asiento import GENESIS
        a = crear_acto_por_codigo(
            "A_FUSION_POR_ABSORCION",
            indice=0, hash_previo=GENESIS, fecha=date(2025, 1, 1),
            valor_razonable_centimos=1_000_000,
            capital_emitido_centimos=500_000,
            prima_centimos=100_000,
        )
        assert a.cuadra

    def test_derivado(self):
        from datetime import date
        from conta_rizoma4.operaciones import crear_acto_por_codigo
        from conta_rizoma4.operativo.asiento import GENESIS
        a = crear_acto_por_codigo(
            "A_VALORACION_DERIVADO_FAVORABLE",
            indice=0, hash_previo=GENESIS, fecha=date(2025, 1, 1),
            importe_centimos=10_000,
        )
        assert a.cuadra
