#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Demo end-to-end del flujo contable completo.

  Fase 1 (devengo):       JustificacionInterna → 4308
  Fase 2 (facturación):   ActoEconomico        → 430
  Fase 3 (cobro):         ActoEconomico        → 572

Los actos se marcan con metadatos={"demo": "flujo_completo"} para
limpiarlos y localizarlos sin depender de índices fijos.

Uso:
    export CONTA_PG_URL=postgresql://rizoma:rizoma_dev@localhost:5433/conta_rizoma4
    python scripts/demo_flujo_completo.py
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import psycopg

from conta_rizoma4.operativo.acto_economico import PG_URL
from conta_rizoma4.operativo.justificacion_interna import (
    crear_justificacion_interna,
    guardar_justificacion_interna,
)
from conta_rizoma4.operativo.reclasificacion import (
    reclasificar_justificacion,
)
from conta_rizoma4.operativo.repositorio_acto import RepositorioActoEconomico


CLIENTE = "Taller RBB SL"
NIF_CLIENTE = "B12345678"
OBRA_REF = "OBRA-2025-01"
IMPORTE_CENTIMOS = 121_000
MARCA_DEMO = {"demo": "flujo_completo"}


def _limpiar_demo() -> None:
    with psycopg.connect(PG_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM acto_economico "
                "WHERE metadatos->>'demo' = 'flujo_completo'"
            )
            cur.execute(
                "DELETE FROM justificacion_interna "
                "WHERE metadatos->>'demo' = 'flujo_completo'"
            )
        conn.commit()


def _actos_del_demo() -> list[dict]:
    with psycopg.connect(PG_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT indice, fecha, cuenta_pgc, cuenta_contrapartida, "
                "       importe_centimos, concepto, hash, hash_previo "
                "FROM acto_economico "
                "WHERE metadatos->>'demo' = 'flujo_completo' "
                "ORDER BY indice"
            )
            return cur.fetchall()


def _pendientes_del_demo() -> list[dict]:
    with psycopg.connect(PG_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT indice, fecha, importe_centimos, concepto "
                "FROM justificacion_interna "
                "WHERE metadatos->>'demo' = 'flujo_completo' "
                "  AND indice NOT IN ("
                "    SELECT justificacion_indice FROM acto_economico "
                "    WHERE justificacion_indice IS NOT NULL"
                "  )"
                "ORDER BY indice"
            )
            return cur.fetchall()


def _header(texto: str) -> None:
    print()
    print("=" * 70)
    print(f"  {texto}")
    print("=" * 70)


def _fmt_eur(centimos: int) -> str:
    signo = "-" if centimos < 0 else ""
    c = abs(centimos)
    return f"{signo}{c // 100}.{c % 100:02d} EUR"


def main() -> int:
    repo = RepositorioActoEconomico()

    _header("LIMPIEZA PREVIA")
    _limpiar_demo()
    print(f"  Actos totales en BD:        {repo.contar()}")
    print(f"  Último índice global:       {repo.ultimo_indice()}")
    print("  (el demo se marca con metadatos {'demo': 'flujo_completo'})")

    # ─── FASE 1 ──────────────────────────────────────────────
    _header("FASE 1 — Obra ejecutada (devengo)")
    print(f"  Cliente:  {CLIENTE} ({NIF_CLIENTE})")
    print(f"  Obra:     {OBRA_REF}")
    print(f"  Importe:  {_fmt_eur(IMPORTE_CENTIMOS)}")
    print(f"  Cuenta:   4308 (Clientes, obra ejecutada pendiente de facturar)")
    print()

    just = crear_justificacion_interna(
        indice=0,  # placeholder; guardar_justificacion_interna no usa el índice fijo
        fecha=date(2025, 3, 31),
        cuenta_pgc="4308",
        importe_centimos=IMPORTE_CENTIMOS,
        concepto=f"Obra {OBRA_REF} — {CLIENTE}",
        creado_por="rubén",
        obra_ref=OBRA_REF,
        contrato_ref="CONTRATO-2025-RBB",
        metadatos=MARCA_DEMO,
    )
    # Recalcular indice (por si acaso el último no es 0)
    with psycopg.connect(PG_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COALESCE(MAX(indice), -1) + 1 FROM justificacion_interna"
            )
            just_indice = cur.fetchone()[0]
    # Recrear con el índice correcto
    just = crear_justificacion_interna(
        indice=just_indice,
        fecha=date(2025, 3, 31),
        cuenta_pgc="4308",
        importe_centimos=IMPORTE_CENTIMOS,
        concepto=f"Obra {OBRA_REF} — {CLIENTE}",
        creado_por="rubén",
        obra_ref=OBRA_REF,
        contrato_ref="CONTRATO-2025-RBB",
        metadatos=MARCA_DEMO,
    )
    guardar_justificacion_interna(just)
    print(f"  ✓ JustificacionInterna #{just.indice} creada")
    print(f"    Huella: {just.huella_contenido[:16]}...")
    print(f"    Hash:   {just.hash[:16]}...")

    # ─── FASE 2 ──────────────────────────────────────────────
    _header("FASE 2 — Facturación (reclasificación del devengo)")
    print(f"  Factura:  F-2025-004")
    print(f"  Fecha:    2025-04-15")
    print(f"  Movimiento: 4308 → 430 (Clientes)")
    print()

    acto_factura = reclasificar_justificacion(
        just,
        creado_por="rubén",
        cuenta_destino="430",
        fecha=date(2025, 4, 15),
        concepto=f"Factura F-2025-004 — {CLIENTE}",
        repo=repo,
        metadatos=MARCA_DEMO,
    )
    print(f"  ✓ ActoEconomico #{acto_factura.indice} creado")
    print(f"    Cuenta:          {acto_factura.cuenta_pgc} (Clientes)")
    print(f"    Contrapartida:   {acto_factura.cuenta_contrapartida} (4308)")
    print(f"    Resuelve just.:  #{acto_factura.justificacion_indice}")
    print(f"    Huella:          {acto_factura.huella_contenido[:16]}...")
    print(f"    Hash:            {acto_factura.hash[:16]}...")
    print(f"    Hash previo:     {acto_factura.hash_previo[:16]}...")

    # ─── FASE 3 ──────────────────────────────────────────────
    _header("FASE 3 — Cobro (430 → 572)")
    print(f"  Fecha:    2025-05-10")
    print(f"  Movimiento: 430 → 572 (Bancos)")
    print()

    acto_cobro = repo.crear_siguiente(
        fecha=date(2025, 5, 10),
        cuenta_pgc="572",
        importe_centimos=IMPORTE_CENTIMOS,
        concepto=f"Cobro factura F-2025-004 — {CLIENTE}",
        creado_por="rubén",
        cuenta_contrapartida="430",
        documento_tipo="EXTRACTO_BANCARIO",
        documento_ref="MOV-2025-05-001",
        metadatos=MARCA_DEMO,
    )
    print(f"  ✓ ActoEconomico #{acto_cobro.indice} creado")
    print(f"    Cuenta:          {acto_cobro.cuenta_pgc} (Bancos)")
    print(f"    Contrapartida:   {acto_cobro.cuenta_contrapartida} (Clientes)")
    print(f"    Hash:            {acto_cobro.hash[:16]}...")
    print(f"    Hash previo:     {acto_cobro.hash_previo[:16]}...")

    # ─── VERIFICACIÓN ────────────────────────────────────────
    _header("VERIFICACIÓN DE LA CADENA DEL DEMO")
    actos_demo = _actos_del_demo()
    print(f"  Actos del demo: {len(actos_demo)}")
    print()
    for a in actos_demo:
        indice, fecha, cuenta, contrapartida, importe, concepto, h, hp = a
        print(
            f"  #{indice:>4}  {fecha}  "
            f"{cuenta:>4} ← {contrapartida or '-':>4}  "
            f"{_fmt_eur(importe):>14}  {concepto[:40]}"
        )
    print()

    verificacion_ok = False
    if actos_demo:
        idxs = [a[0] for a in actos_demo]
        rep = repo.verificar_cadena(desde=idxs[0], hasta=idxs[-1])
        if rep.cadena_valida:
            print(f"  ✓ Cadena VÁLIDA  ({rep.total} actos verificados)")
            verificacion_ok = True
        else:
            print(f"  ✗ Cadena ROTA  ({rep.total} actos)")
            for r in rep.roturas:
                print(f"    ✗ {r}")

    # ─── PENDIENTES DEL DEMO ────────────────────────────────
    _header("JUSTIFICACIONES DEL DEMO PENDIENTES DE FACTURAR")
    pend = _pendientes_del_demo()
    if not pend:
        print("  (ninguna — todo facturado)")
    else:
        for p in pend:
            print(f"  #{p['indice']}  {p['fecha']}  {_fmt_eur(p['importe_centimos'])}  {p['concepto']}")

    # ─── RESUMEN ────────────────────────────────────────────
    _header("RESUMEN")
    print(f"  Obra devengada:    {_fmt_eur(IMPORTE_CENTIMOS)} en 4308")
    print(f"  Facturada:         {_fmt_eur(IMPORTE_CENTIMOS)} de 4308 a 430")
    print(f"  Cobrada:           {_fmt_eur(IMPORTE_CENTIMOS)} de 430 a 572")
    print(f"  Pendiente:         {len(pend)} justificación(es)")
    print()

    if verificacion_ok and len(actos_demo) == 2 and not pend:
        print("  ✓ Flujo completo verificado.")
        return 0
    else:
        print("  ✗ Flujo NO verificado.")
        return 1


if __name__ == "__main__":
    sys.exit(main())