# -*- coding: utf-8 -*-
"""CLI de conta-rizoma4.

Comandos:
  sugerir       A+B+C → D (cuenta PGC) con justificación doctrinal
  justificar    Crea una JustificacionInterna (devengo, obra ejecutada)
  crear         Crea un ActoEconomico manual
  reclasificar  Resuelve una JustificacionInterna con un acto
  listar        Lista actos con filtros
  ver           Muestra un acto por índice
  verificar     Verifica la integridad de la cadena
  pendientes    Justificaciones pendientes de facturar

Uso:
  conta sugerir --doc FACTURA_EMITIDA --int JURIDICA
  conta justificar --cuenta 4308 --importe 1210.00 --concepto "Obra X" --obra OBRA-01 --por "rubén"
  conta crear --cuenta 705 --importe 1210.00 --concepto "Factura" --por "rubén"
  conta reclasificar --justificacion 9001 --por "rubén"
  conta listar [--cuenta 705] [--desde 0] [--hasta 100]
  conta ver --indice 5
  conta verificar [--desde 0] [--hasta 100]
  conta pendientes
"""
from __future__ import annotations

import argparse
import sys
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

from .operativo.acto_economico import leer_ultimo_acto
from .operativo.justificacion_interna import (
    crear_justificacion_interna,
    guardar_justificacion_interna,
)
from .operativo.mapeo_abcd import sugerir_cuenta_pgc
from .operativo.reclasificacion import (
    ReclasificacionError,
    justificaciones_pendientes,
    reclasificar_justificacion,
)
from .operativo.repositorio_acto import RepositorioActoEconomico
from .cli_pd import registrar_subcomandos


def _aviso_deprecated(nombre_antiguo: str, nombre_nuevo: str) -> None:
    """Aviso a stderr cuando se usa un comando del POC."""
    print(
        f"[DEPRECATED] '{nombre_antiguo}' usa el modelo antiguo. "
        f"Usa '{nombre_nuevo}' (partida doble).",
        file=sys.stderr,
    )


# ─── Utilidades ────────────────────────────────────────────────────

def _parse_importe(s: str) -> int:
    """'1210.00' → 121000 (céntimos). Nunca float."""
    try:
        d = Decimal(s)
    except InvalidOperation:
        raise argparse.ArgumentTypeError(f"importe inválido: {s!r}")
    if d < 0:
        raise argparse.ArgumentTypeError("el importe no puede ser negativo")
    return int(d * 100)


def _parse_fecha(s: str) -> date:
    """'2025-04-15' → date(2025, 4, 15)."""
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"fecha inválida: {s!r} (formato YYYY-MM-DD)"
        )


def _fmt_eur(centimos: int) -> str:
    signo = "-" if centimos < 0 else ""
    c = abs(centimos)
    return f"{signo}{c // 100}.{c % 100:02d} EUR"


# ─── Handlers ──────────────────────────────────────────────────────

def _cmd_sugerir(args) -> int:
    s = sugerir_cuenta_pgc(
        documento_tipo=args.doc,
        interlocutor_tipo=args.int,
        actividad_nivel1=args.actividad,
    )
    print(f"Documento:       {args.doc}")
    print(f"Interlocutor:    {args.int or '(wildcard)'}")
    print(f"Actividad:       {args.actividad or '(wildcard)'}")
    print()
    print(f"Cuenta PGC:      {s.cuenta.cuenta}")
    print(f"Descripción:     {s.cuenta.descripcion}")
    print(f"Confianza:       {s.confianza:.2f}")
    print(f"Motivo:          {s.motivo}")
    if s.parrafo_pgc:
        p = s.parrafo_pgc
        print()
        print(f"Justificación doctrinal (PGC pág. {p['n_pg']}, línea {p['n_linea']}):")
        print(f"  {p['texto'][:300]}{'...' if len(p['texto']) > 300 else ''}")
    return 0


def _cmd_justificar(args) -> int:
    repo = RepositorioActoEconomico()
    # Calcular el siguiente índice de justificación
    import psycopg
    from .operativo.acto_economico import PG_URL
    with psycopg.connect(PG_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COALESCE(MAX(indice), -1) + 1 FROM justificacion_interna"
            )
            indice = cur.fetchone()[0]
    just = crear_justificacion_interna(
        indice=indice,
        fecha=args.fecha or date.today(),
        cuenta_pgc=args.cuenta,
        importe_centimos=args.importe,
        concepto=args.concepto,
        creado_por=args.por,
        obra_ref=args.obra,
        contrato_ref=args.contrato,
    )
    guardar_justificacion_interna(just)
    print(f"✓ JustificacionInterna #{just.indice} creada")
    print(f"  Cuenta:   {just.cuenta_pgc}")
    print(f"  Importe:  {_fmt_eur(just.importe_centimos)}")
    print(f"  Concepto: {just.concepto}")
    print(f"  Obra:     {just.obra_ref or '-'}")
    print(f"  Hash:     {just.hash[:16]}...")
    return 0


def _cmd_crear(args) -> int:
    repo = RepositorioActoEconomico()
    acto = repo.crear_siguiente(
        fecha=args.fecha or date.today(),
        cuenta_pgc=args.cuenta,
        importe_centimos=args.importe,
        concepto=args.concepto,
        creado_por=args.por,
        cuenta_contrapartida=args.contrapartida,
        documento_tipo=args.doc,
        documento_ref=args.ref,
    )
    print(f"✓ ActoEconomico #{acto.indice} creado")
    print(f"  Cuenta:        {acto.cuenta_pgc}")
    if acto.cuenta_contrapartida:
        print(f"  Contrapartida: {acto.cuenta_contrapartida}")
    print(f"  Importe:       {_fmt_eur(acto.importe_centimos)}")
    print(f"  Concepto:      {acto.concepto}")
    print(f"  Fecha:         {acto.fecha}")
    print(f"  Hash:          {acto.hash[:16]}...")
    print(f"  Hash previo:   {acto.hash_previo[:16]}...")
    return 0


def _cmd_reclasificar(args) -> int:
    import psycopg
    from .operativo.acto_economico import PG_URL
    from .operativo.justificacion_interna import JustificacionInterna

    with psycopg.connect(PG_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT indice, fecha, cuenta_pgc, importe_centimos, "
                "concepto, obra_ref, contrato_ref, creado_por, "
                "huella_contenido, hash_previo, hash "
                "FROM justificacion_interna WHERE indice = %s",
                (args.justificacion,),
            )
            row = cur.fetchone()
    if row is None:
        print(f"✗ JustificacionInterna #{args.justificacion} no encontrada",
              file=sys.stderr)
        return 1

    just = JustificacionInterna(
        indice=row[0], fecha=row[1], cuenta_pgc=row[2],
        importe_centimos=row[3], concepto=row[4],
        obra_ref=row[5], contrato_ref=row[6],
        creado_por=row[7], huella_contenido=row[8],
        hash_previo=row[9], hash=row[10],
    )
    try:
        acto = reclasificar_justificacion(
            just, creado_por=args.por,
            cuenta_destino=args.cuenta,
            fecha=args.fecha,
        )
    except ReclasificacionError as e:
        print(f"✗ {e}", file=sys.stderr)
        return 1

    print(f"✓ ActoEconomico #{acto.indice} creado (reclasifica #{just.indice})")
    print(f"  De:    {just.cuenta_pgc} ({_fmt_eur(just.importe_centimos)})")
    print(f"  A:     {acto.cuenta_pgc}")
    print(f"  Hash:  {acto.hash[:16]}...")
    return 0


def _cmd_listar(args) -> int:
    repo = RepositorioActoEconomico()
    actos = repo.listar(
        indice_desde=args.desde,
        indice_hasta=args.hasta,
        cuenta=args.cuenta,
        limite=args.limite,
    )
    if not actos:
        print("(sin actos)")
        return 0
    print(f"{'#':>5}  {'fecha':<10}  {'cuenta':>6}  {'contra':>6}  "
          f"{'importe':>14}  concepto")
    print("-" * 100)
    for a in actos:
        print(
            f"{a['indice']:>5}  {a['fecha']!s:<10}  {a['cuenta_pgc']:>6}  "
            f"{(a['cuenta_contrapartida'] or '-'):>6}  "
            f"{_fmt_eur(a['importe_centimos']):>14}  {a['concepto'][:50]}"
        )
    print()
    print(f"Total: {len(actos)} acto(s)")
    return 0


def _cmd_ver(args) -> int:
    repo = RepositorioActoEconomico()
    a = repo.obtener(args.indice)
    if a is None:
        print(f"✗ Acto #{args.indice} no encontrado", file=sys.stderr)
        return 1
    print(f"ActoEconomico #{a['indice']}")
    print("─" * 70)
    for k, v in a.items():
        if k in ("metadatos",) and v:
            v = f"{v}"[:80]
        print(f"  {k:25s} {v}")
    return 0


def _cmd_verificar(args) -> int:
    repo = RepositorioActoEconomico()
    rep = repo.verificar_cadena(desde=args.desde, hasta=args.hasta)
    print(f"Actos verificados: {rep.total}")
    print(f"Rango:             [{rep.desde}, {rep.hasta}]")
    print()
    if rep.cadena_valida:
        print("✓ Cadena VÁLIDA")
        return 0
    print(f"✗ Cadena ROTA ({len(rep.roturas)} rotura(s)):")
    for r in rep.roturas:
        print(f"  - acto #{r['indice']}: {r['tipo']}")
        if "esperado" in r:
            print(f"    esperado: {r['esperado'][:32]}...")
            print(f"    guardado: {r['guardado'][:32]}...")
    return 1


def _cmd_pendientes(args) -> int:
    pend = justificaciones_pendientes()
    if not pend:
        print("(ninguna justificación pendiente — todo facturado)")
        return 0
    print(f"{'#':>5}  {'fecha':<10}  {'importe':>14}  concepto")
    print("-" * 80)
    for p in pend:
        print(
            f"{p['indice']:>5}  {p['fecha']!s:<10}  "
            f"{_fmt_eur(p['importe_centimos']):>14}  {p['concepto'][:45]}"
        )
    print()
    print(f"Total: {len(pend)} pendiente(s)")
    return 0


def _cmd_reset(args) -> int:
    """Comando retirado: el ledger se conserva y se corrige append-only."""
    print("reset está deshabilitado; los registros contables no se borran físicamente.")
    return 2


# ─── Parser ────────────────────────────────────────────────────────

def _construir_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="conta",
        description="conta-rizoma4: contabilidad doctrinal sobre el PGC.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    # sugerir
    sp = sub.add_parser("sugerir", help="[DEPRECATED] Usa pd-acto. Sugiere cuenta PGC")
    sp.add_argument("--doc", required=True, help="Tipo de documento (C)")
    sp.add_argument("--int", help="Tipo de interlocutor (B)", default=None)
    sp.add_argument("--actividad", help="Nivel1 (A)", default=None)
    sp.set_defaults(handler=_cmd_sugerir)

    # justificar
    sp = sub.add_parser("justificar", help="[DEPRECATED] Crea JustificacionInterna")
    sp.add_argument("--cuenta", required=True)
    sp.add_argument("--importe", required=True, type=_parse_importe)
    sp.add_argument("--concepto", required=True)
    sp.add_argument("--por", required=True, dest="por")
    sp.add_argument("--obra")
    sp.add_argument("--contrato")
    sp.add_argument("--fecha", type=_parse_fecha)
    sp.set_defaults(handler=_cmd_justificar)

    # crear
    sp = sub.add_parser("crear", help="[DEPRECATED] Usa pd-acto crear")
    sp.add_argument("--cuenta", required=True)
    sp.add_argument("--importe", required=True, type=_parse_importe)
    sp.add_argument("--concepto", required=True)
    sp.add_argument("--por", required=True, dest="por")
    sp.add_argument("--contrapartida")
    sp.add_argument("--doc")
    sp.add_argument("--ref")
    sp.add_argument("--fecha", type=_parse_fecha)
    sp.set_defaults(handler=_cmd_crear)

    # reclasificar
    sp = sub.add_parser("reclasificar", help="[DEPRECATED] Reclasifica una JustificacionInterna")
    sp.add_argument("--justificacion", type=int, required=True)
    sp.add_argument("--por", required=True, dest="por")
    sp.add_argument("--cuenta", default="430")
    sp.add_argument("--fecha", type=_parse_fecha)
    sp.set_defaults(handler=_cmd_reclasificar)

    # listar
    sp = sub.add_parser("listar", help="[DEPRECATED] Usa pd-diario")
    sp.add_argument("--desde", type=int)
    sp.add_argument("--hasta", type=int)
    sp.add_argument("--cuenta")
    sp.add_argument("--limite", type=int, default=100)
    sp.set_defaults(handler=_cmd_listar)

    # ver
    sp = sub.add_parser("ver", help="[DEPRECATED] Usa pd-diario")
    sp.add_argument("--indice", type=int, required=True)
    sp.set_defaults(handler=_cmd_ver)

    # verificar
    sp = sub.add_parser("verificar", help="[DEPRECATED] Usa pd-verificar")
    sp.add_argument("--desde", type=int)
    sp.add_argument("--hasta", type=int)
    sp.set_defaults(handler=_cmd_verificar)

    # pendientes
    sp = sub.add_parser("pendientes", help="[DEPRECATED] Justificaciones pendientes")
    sp.set_defaults(handler=_cmd_pendientes)

    # reset
    sp = sub.add_parser("reset", help="Retirado: no borra datos contables")
    sp.add_argument("--yes", action="store_true", help="Confirmar borrado")
    sp.set_defaults(handler=_cmd_reset)

    registrar_subcomandos(sub)
    return p


def main(argv: Optional[list[str]] = None) -> int:
    parser = _construir_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except KeyboardInterrupt:
        print("\nInterrumpido.", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
