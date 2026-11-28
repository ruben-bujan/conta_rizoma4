#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Demo completo de conta-rizoma4.

Caso realista: Taller RBB SL — Q1 2025.
(Docstring original intacto)
"""
from __future__ import annotations

import os
import sys

# ═══════════════════════════════════════════════════════════════════════════
# GUARDIA ANTI-PRODUCCIÓN — DEBE IR ANTES DE CUALQUIER import de conta_rizoma4
# ═══════════════════════════════════════════════════════════════════════════
_PROD_MARKERS = ("prod", "production", "-live", "_live", "prd")


def _bail(msg: str, code: int = 1) -> "None":
    print(msg, file=sys.stderr)
    sys.exit(code)


if os.environ.get("CONTA_DEMO_OK") != "1":
    _bail(
        "❌ demo_completo.py requiere CONTA_DEMO_OK=1 (evita ejecución accidental).\n"
        "   export CONTA_DEMO_OK=1 && python scripts/demo_completo.py"
    )

for _var in ("CONTA_PG_URL", "CONTA_PG_HOST", "CONTA_PG_DB"):
    _val = os.environ.get(_var, "").lower()
    if _val and any(m in _val for m in _PROD_MARKERS):
        _bail(f"❌ {_var}={os.environ[_var]!r} parece producción. Abortando.")

# ── a partir de aquí, ya es seguro importar conta_rizoma4 ─────────────────
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import psycopg

from conta_rizoma4.operaciones import crear_acto_por_codigo
from conta_rizoma4.partida_doble import (
    guardar_asiento, RepositorioAsiento,
    listar_diario, totales_diario,
    mayor, balance_comprobacion,
    balance_situacion, cuenta_pyg,
)
from conta_rizoma4.operativo.asiento import GENESIS
import os
_PROD_MARKERS = ("prod", "production", "-live", "_live", "prd")
def _assert_non_prod() -> None:
    """Aborta si la BD parece producción. Doble check: URL + current_database()."""
    if os.environ.get("CONTA_DEMO_OK") != "1":
        sys.exit(
            "❌ demo_completo.py requiere CONTA_DEMO_OK=1 (evita ejecución accidental).\n"
            "   export CONTA_DEMO_OK=1 && python scripts/demo_completo.py"
        )
    url = os.environ.get("CONTA_PG_URL", "")
    low = url.lower()
    if any(m in low for m in _PROD_MARKERS):
        sys.exit(f"❌ CONTA_PG_URL parece producción: {url!r}")
    with psycopg.connect(url) as conn, conn.cursor() as cur:
        cur.execute("SELECT current_database()")
        db = cur.fetchone()[0]
    if any(m in db.lower() for m in _PROD_MARKERS):
        sys.exit(f"❌ current_database()={db!r} parece producción")

def _crear(repo: RepositorioAsiento, codigo: str, **params):
    ultimo = repo.ultimo_indice()
    ultimo_data = repo.obtener(ultimo) if ultimo >= 0 else None
    hash_previo = ultimo_data["hash"] if ultimo_data else GENESIS
    acto = crear_acto_por_codigo(
        codigo, indice=ultimo + 1, hash_previo=hash_previo, **params,
    )
    guardar_asiento(acto)
    return acto


def _header(titulo: str) -> None:
    print()
    print("=" * 70)
    print(f"  {titulo}")
    print("=" * 70)


def _fmt(centimos: int) -> str:
    signo = "-" if centimos < 0 else ""
    c = abs(centimos)
    return f"{signo}{c // 100}.{c % 100:02d}"


def main() -> int:
    repo = RepositorioAsiento()
    print(f"Estado inicial: {repo.contar()} asientos en la BD")

    # ─── Q1 2025 ──────────────────────────────────────────────
    _header("Q1 2025 — Taller RBB SL")

    print("\n[Enero 2025]")
    _crear(repo, "A_FACT_EMIT_SERV_NAC_SIN_RET",
        fecha=date(2025, 1, 15), base_centimos=100_000, iva_pct=21,
        cliente_nif=CLIENTE_A, concepto="Factura F-2025-001")
    print("  ✓ Factura F-2025-001 a cliente A: 1.000,00 + IVA")

    _crear(repo, "A_FACT_REC_GASTO_NAC",
        fecha=date(2025, 1, 20), base_centimos=50_000, iva_pct=21,
        cuenta_gasto="600", proveedor_nif=PROVEEDOR_B,
        concepto="Compra material")
    print("  ✓ Compra material a proveedor B: 500,00 + IVA")

    _crear(repo, "A_NOMINA_MENSUAL",
        fecha=date(2025, 1, 31), bruto_centimos=200_000,
        irpf_pct=15, ss_trabajador_pct=6.35, ss_empresa_pct=30,
        trabajador_nif=EMPLEADO_C, concepto="Nómina enero 2025")
    print("  ✓ Nómina enero: 2.000,00 bruto")

    print("\n[Febrero 2025]")
    _crear(repo, "A_FACT_EMIT_SERV_NAC_SIN_RET",
        fecha=date(2025, 2, 15), base_centimos=200_000, iva_pct=21,
        cliente_nif=CLIENTE_D, concepto="Factura F-2025-002")
    print("  ✓ Factura F-2025-002 a cliente D: 2.000,00 + IVA")

    _crear(repo, "A_COMPRA_INMOV_MATERIAL",
        fecha=date(2025, 2, 28), base_centimos=120_000, iva_pct=21,
        cuenta_inmov="217", proveedor_nif=PROVEEDOR_INMOV,
        concepto="Compra ordenador portátil")
    print("  ✓ Compra ordenador: 1.200,00 + IVA")

    print("\n[Marzo 2025]")
    _crear(repo, "A_COBRO_CLIENTE_TRANSF",
        fecha=date(2025, 3, 15), importe_centimos=121_000,
        cliente_nif=CLIENTE_A, concepto="Cobro F-2025-001")
    print("  ✓ Cobro cliente A: 1.210,00")

    _crear(repo, "A_FACT_EMIT_SERV_NAC_SIN_RET",
        fecha=date(2025, 3, 20), base_centimos=150_000, iva_pct=21,
        cliente_nif=CLIENTE_E, concepto="Factura F-2025-003")
    print("  ✓ Factura F-2025-003 a cliente E: 1.500,00 + IVA")

    _crear(repo, "A_AMORTIZACION_ANUAL",
        fecha=date(2025, 3, 31), importe_centimos=7_500,
        cuenta_gasto="681", cuenta_amort="281",
        concepto="Amortización Q1 ordenador")
    print("  ✓ Amortización Q1: 75,00")

    print("\n[Abril 2025]")
    _crear(repo, "A_COBRO_CLIENTE_TRANSF",
        fecha=date(2025, 4, 10), importe_centimos=242_000,
        cliente_nif=CLIENTE_D, concepto="Cobro F-2025-002")
    print("  ✓ Cobro cliente D: 2.420,00")

    # Liquidación IVA calculada dinámicamente
    m_iva = mayor(repo)
    iva_rep = -m_iva.get("477", {}).get("saldo", 0)
    iva_sop = m_iva.get("472", {}).get("saldo", 0)
    _crear(repo, "A_LIQ_IVA_TRIM_303_INGRESAR",
        fecha=date(2025, 4, 20),
        iva_repercutido_centimos=iva_rep,
        iva_soportado_centimos=iva_sop,
        concepto="Liquidación IVA Q1 2025 (303)")
    print(f"  ✓ Liquidación IVA Q1: {_fmt(iva_rep)} rep. - {_fmt(iva_sop)} sop. = {_fmt(iva_rep - iva_sop)} a ingresar")

    # ─── Diario ──────────────────────────────────────────────
    _header(f"DIARIO ({repo.contar()} asientos)")
    for a in listar_diario(repo):
        print(f"\n#{a['indice']}  {a['fecha']}  {a['concepto']}")
        for l in a["lineas"]:
            if l["debe_centimos"] > 0:
                print(f"  D {l['cuenta_pgc']:>6}  {_fmt(l['debe_centimos']):>12}")
            else:
                print(f"  H {l['cuenta_pgc']:>6}  {_fmt(l['haber_centimos']):>12}")

    t = totales_diario(listar_diario(repo))
    print(f"\n{'-'*54}")
    print(f"Total debe:  {_fmt(t['total_debe']):>12}")
    print(f"Total haber: {_fmt(t['total_haber']):>12}")
    print(f"Cuadra:      {'✓' if t['cuadra'] else '✗'}")

    # ─── Mayor ───────────────────────────────────────────────
    _header("MAYOR")
    m = mayor(repo)
    print(f"{'cuenta':>8}  {'debe':>12}  {'haber':>12}  {'saldo':>12}")
    print("-" * 54)
    for c in sorted(m.keys()):
        d = m[c]
        print(f"{c:>8}  {_fmt(d['debe']):>12}  {_fmt(d['haber']):>12}  {_fmt(d['saldo']):>12}")

    # ─── Balance ─────────────────────────────────────────────
    _header("BALANCE DE COMPROBACIÓN")
    b = balance_comprobacion(repo)
    print(f"Total debe:  {_fmt(b['total_debe']):>12}")
    print(f"Total haber: {_fmt(b['total_haber']):>12}")
    print(f"Cuadre:      {'✓' if b['cuadra'] else '✗'}")

    # ─── PyG ─────────────────────────────────────────────────
    _header("CUENTA DE PÉRDIDAS Y GANANCIAS")
    p = cuenta_pyg(repo)
    print("GASTOS:")
    for c in sorted(p["gastos"]):
        print(f"  {c:>8}  {_fmt(p['gastos'][c]):>14}")
    print(f"  {'Total':>8}  {_fmt(p['total_gastos']):>14}")
    print("\nINGRESOS:")
    for c in sorted(p["ingresos"]):
        print(f"  {c:>8}  {_fmt(p['ingresos'][c]):>14}")
    print(f"  {'Total':>8}  {_fmt(p['total_ingresos']):>14}")
    print(f"\nRESULTADO:  {_fmt(p['resultado']):>14}  "
          f"({'beneficio' if p['resultado'] >= 0 else 'pérdida'})")

    # ─── Situación ───────────────────────────────────────────
    _header("BALANCE DE SITUACIÓN")
    s = balance_situacion(repo)
    print("ACTIVO:")
    for c in sorted(s["activo"]):
        print(f"  {c:>8}  {_fmt(s['activo'][c]):>14}")
    if s.get("correctores"):
        print("  Correctores (se restan):")
        for c in sorted(s["correctores"]):
            print(f"  ({c:>7})  {_fmt(-s['correctores'][c]):>13}")
    print(f"  {'Total':>8}  {_fmt(s['total_activo']):>14}")
    print("\nPASIVO + PN:")
    for c in sorted(s["pasivo"]):
        print(f"  {c:>8}  {_fmt(s['pasivo'][c]):>14}")
    print(f"  {'Resultado':>8}  {_fmt(s['resultado_ejercicio']):>14}")
    print(f"  {'Total':>8}  {_fmt(s['total_pasivo_mas_resultado']):>14}")
    print(f"\nCuadre: {'✓' if s['cuadra'] else '✗'}")

    _header("VERIFICACIÓN DE CADENA")
    rep = repo.verificar_cadena()
    print(f"Asientos: {rep.total}")
    print(f"Cadena:   {'✓ VÁLIDA' if rep.cadena_valida else '✗ ROTA'}")

    print()
    print("✓ Demo completo. Sistema operativo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
