# -*- coding: utf-8 -*-
"""Comandos CLI sobre partida doble (Ciclo 11).

  conta pd-acto listar [--grupo G]
  conta pd-acto crear CODIGO --json '{...}'
  conta pd-diario [--desde N] [--hasta N]
  conta pd-mayor [--cuenta X]
  conta pd-balance
  conta pd-pyg
  conta pd-situacion
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from .actos.catalogo import CATALOGO, listar_grupos, listar_por_grupo, obtener
from .partida_doble import (
    crear_asiento, guardar_asiento, RepositorioAsiento,
    ReporteCadenaAsientos,
    listar_diario, totales_diario,
    mayor, balance_comprobacion,
    balance_situacion, cuenta_pyg,
    balance_formateado, pyg_formateado,
)
from .operativo.asiento import GENESIS


def _fmt_eur(centimos: int) -> str:
    signo = "-" if centimos < 0 else ""
    c = abs(centimos)
    return f"{signo}{c // 100}.{c % 100:02d}"


def _parse_parametros_json(raw: str) -> dict:
    """Parsea JSON, convierte floats monetarios a céntimos int."""
    try:
        d = json.loads(raw)
    except json.JSONDecodeError as e:
        raise SystemExit(f"JSON inválido: {e}")
    # fecha
    if "fecha" in d:
        d["fecha"] = datetime.strptime(d["fecha"], "%Y-%m-%d").date()
    # importes: los que acaben en _centimos ya son int.
    # Los _pct se dejan como float.
    return d


def _crear_asiento_desde_acto(codigo: str, params: dict, repo) -> dict:
    """Crea el asiento con el dispatcher, leyendo hash_previo del último."""
    grupo, fn = obtener(codigo)
    ultimo_idx = repo.ultimo_indice()
    ultimo = repo.obtener(ultimo_idx) if ultimo_idx >= 0 else None
    hash_previo = ultimo["hash"] if ultimo else GENESIS
    indice = ultimo_idx + 1
    params_completos = {
        "indice": indice,
        "hash_previo": hash_previo,
        **params,
    }
    try:
        asiento = fn(**params_completos)
    except TypeError as e:
        raise SystemExit(f"Parámetros incorrectos para {codigo}: {e}")
    except ValueError as e:
        raise SystemExit(f"Error de validación: {e}")
    guardar_asiento(asiento)
    return {
        "indice": asiento.indice,
        "codigo": codigo,
        "grupo": grupo,
        "hash": asiento.hash,
        "n_lineas": len(asiento.lineas),
    }


# ─── Handlers ──────────────────────────────────────────────────

def _cmd_pd_acto_listar(args) -> int:
    if args.grupo:
        codigos = listar_por_grupo(args.grupo)
        print(f"Grupo: {args.grupo} ({len(codigos)} actos)")
        for c in codigos:
            print(f"  {c}")
    else:
        print(f"Catálogo: {len(CATALOGO)} actos en {len(listar_grupos())} grupos\n")
        for g in listar_grupos():
            codigos = listar_por_grupo(g)
            print(f"[{g}] ({len(codigos)})")
            for c in codigos:
                print(f"  {c}")
            print()
    return 0


def _cmd_pd_acto_crear(args) -> int:
    repo = RepositorioAsiento('default')
    params = _parse_parametros_json(args.json)
    resultado = _crear_asiento_desde_acto(args.codigo, params, repo)
    print(f"✓ Asiento #{resultado['indice']} creado")
    print(f"  Código:   {resultado['codigo']}")
    print(f"  Grupo:    {resultado['grupo']}")
    print(f"  Líneas:   {resultado['n_lineas']}")
    print(f"  Hash:     {resultado['hash'][:16]}...")
    return 0


def _cmd_pd_diario(args) -> int:
    repo = RepositorioAsiento('default')
    asientos = listar_diario(repo, desde=args.desde, hasta=args.hasta)
    if not asientos:
        print("(diario vacío)")
        return 0
    for a in asientos:
        print(f"\n#{a['indice']}  {a['fecha']}  {a['concepto']}")
        for l in a["lineas"]:
            if l["debe_centimos"] > 0:
                print(f"  D {l['cuenta_pgc']:>6}  {_fmt_eur(l['debe_centimos']):>12}")
            else:
                print(f"  H {l['cuenta_pgc']:>6}  {_fmt_eur(l['haber_centimos']):>12}")
    t = totales_diario(asientos)
    print(f"\n{'-'*50}")
    print(f"Total debe:  {_fmt_eur(t['total_debe']):>12}")
    print(f"Total haber: {_fmt_eur(t['total_haber']):>12}")
    print(f"Cuadra:      {'✓' if t['cuadra'] else '✗'}")
    return 0


def _cmd_pd_mayor(args) -> int:
    repo = RepositorioAsiento('default')
    m = mayor(repo, desde=args.desde, hasta=args.hasta)
    if args.cuenta:
        if args.cuenta not in m:
            print(f"(cuenta {args.cuenta} sin movimientos)")
            return 0
        d = m[args.cuenta]
        print(f"Cuenta {args.cuenta}")
        print(f"  Debe:  {_fmt_eur(d['debe']):>12}")
        print(f"  Haber: {_fmt_eur(d['haber']):>12}")
        print(f"  Saldo: {_fmt_eur(d['saldo']):>12}")
        print(f"  Movimientos: {len(d['movimientos'])}")
    else:
        print(f"{'cuenta':>8}  {'debe':>12}  {'haber':>12}  {'saldo':>12}")
        print("-" * 54)
        for cuenta in sorted(m.keys()):
            d = m[cuenta]
            print(
                f"{cuenta:>8}  {_fmt_eur(d['debe']):>12}  "
                f"{_fmt_eur(d['haber']):>12}  {_fmt_eur(d['saldo']):>12}"
            )
    return 0


def _cmd_pd_balance(args) -> int:
    repo = RepositorioAsiento('default')
    b = balance_comprobacion(repo, desde=args.desde, hasta=args.hasta)
    print(f"{'cuenta':>8}  {'debe':>12}  {'haber':>12}  {'saldo':>12}")
    print("-" * 54)
    for cuenta in sorted(b["cuentas"].keys()):
        d = b["cuentas"][cuenta]
        print(
            f"{cuenta:>8}  {_fmt_eur(d['debe']):>12}  "
            f"{_fmt_eur(d['haber']):>12}  {_fmt_eur(d['saldo']):>12}"
        )
    print("-" * 54)
    print(f"{'TOTAL':>8}  {_fmt_eur(b['total_debe']):>12}  "
          f"{_fmt_eur(b['total_haber']):>12}")
    print(f"Cuadre: {'✓' if b['cuadra'] else '✗'}")
    return 0


def _cmd_pd_pyg(args) -> int:
    repo = RepositorioAsiento('default')
    p = cuenta_pyg(repo, desde=args.desde, hasta=args.hasta)
    print("GASTOS (grupo 6)")
    print("-" * 40)
    for c in sorted(p["gastos"]):
        print(f"  {c:>8}  {_fmt_eur(p['gastos'][c]):>14}")
    print(f"  {'Total':>8}  {_fmt_eur(p['total_gastos']):>14}")
    print()
    print("INGRESOS (grupo 7)")
    print("-" * 40)
    for c in sorted(p["ingresos"]):
        print(f"  {c:>8}  {_fmt_eur(p['ingresos'][c]):>14}")
    print(f"  {'Total':>8}  {_fmt_eur(p['total_ingresos']):>14}")
    print()
    print(f"RESULTADO:  {_fmt_eur(p['resultado']):>14}  "
          f"({'beneficio' if p['resultado'] >= 0 else 'pérdida'})")
    return 0


def _cmd_pd_situacion(args) -> int:
    repo = RepositorioAsiento('default')
    b = balance_situacion(repo, desde=args.desde, hasta=args.hasta)
    print("ACTIVO")
    print("-" * 40)
    for c in sorted(b["activo"]):
        print(f"  {c:>8}  {_fmt_eur(b['activo'][c]):>14}")
    if b.get("correctores"):
        print()
        print("  Correctores del activo (se restan):")
        for c in sorted(b["correctores"]):
            print(f"  ({c:>7})  {_fmt_eur(-b['correctores'][c]):>13}")
    print(f"  {'Total':>8}  {_fmt_eur(b['total_activo']):>14}")
    print()
    print("PASIVO + PN")
    print("-" * 40)
    for c in sorted(b["pasivo"]):
        print(f"  {c:>8}  {_fmt_eur(b['pasivo'][c]):>14}")
    print(f"  {'Resultado':>8}  {_fmt_eur(b['resultado_ejercicio']):>14}")
    print(f"  {'Total':>8}  {_fmt_eur(b['total_pasivo_mas_resultado']):>14}")
    print()
    print(f"Cuadre: {'✓' if b['cuadra'] else '✗'}")
    return 0


def _cmd_pd_verificar(args) -> int:
    """Verifica la cadena de asientos (partida doble)."""
    repo = RepositorioAsiento('default')
    rep = repo.verificar_cadena(desde=args.desde, hasta=args.hasta)
    print(f"Asientos verificados: {rep.total}")
    print(f"Rango:               [{rep.desde}, {rep.hasta}]")
    print()
    if rep.cadena_valida:
        print("✓ Cadena VÁLIDA (partida doble)")
        return 0
    print(f"✗ Cadena ROTA ({len(rep.roturas)} rotura(s)):")
    for r in rep.roturas:
        print(f"  - asiento #{r['indice']}: {r['tipo']}")
        if "esperado" in r:
            print(f"    esperado: {r['esperado'][:32]}...")
            print(f"    guardado: {r['guardado'][:32]}...")
    return 1


def _cmd_pd_reset(args) -> int:
    """Comando retirado: los asientos se corrigen con reversiones append-only."""
    print("pd-reset está deshabilitado; usa asientos de reversión para corregir registros.")
    return 2


def _cmd_pd_balance_formateado(args) -> int:
    """Balance agrupado por grupos PGC."""
    from .partida_doble.presentacion import _GRUPOS_ACTIVO, _GRUPOS_PYG
    repo = RepositorioAsiento('default')
    b = balance_formateado(repo, desde=args.desde, hasta=args.hasta)

    print("BALANCE DE SITUACIÓN (agrupado por grupos PGC)")
    print("=" * 60)
    print()
    print("ACTIVO")
    print("-" * 60)
    for grupo_num in sorted(b["activo"].keys()):
        cuentas = b["activo"][grupo_num]
        if not cuentas:
            continue
        print(f"Grupo {grupo_num} - {_GRUPOS_ACTIVO[grupo_num]}:")
        for c in sorted(cuentas.keys()):
            print(f"  {c:>8}  {_fmt_eur(cuentas[c]):>14}")
        print(f"  {'Subtotal':>8}  {_fmt_eur(sum(cuentas.values())):>14}")
    if b["correctores"]:
        print()
        print("Correctores del activo (se restan):")
        for c in sorted(b["correctores"].keys()):
            print(f"  ({c:>7})  {_fmt_eur(-b['correctores'][c]):>13}")
        print(f"  {'Subtotal':>8}  {_fmt_eur(-sum(b['correctores'].values())):>14}")
    print("-" * 60)
    print(f"{'TOTAL ACTIVO':>10}  {_fmt_eur(b['total_activo']):>14}")
    print()

    print("PASIVO + PN")
    print("-" * 60)
    for grupo_num in sorted(b["pasivo"].keys()):
        cuentas = b["pasivo"][grupo_num]
        if not cuentas:
            continue
        print(f"Grupo {grupo_num} - {_GRUPOS_ACTIVO[grupo_num]}:")
        for c in sorted(cuentas.keys()):
            print(f"  {c:>8}  {_fmt_eur(cuentas[c]):>14}")
        print(f"  {'Subtotal':>8}  {_fmt_eur(sum(cuentas.values())):>14}")
    print(f"  {'Resultado':>8}  {_fmt_eur(b['resultado_ejercicio']):>14}")
    print("-" * 60)
    print(f"{'TOTAL P+PN':>10}  {_fmt_eur(b['total_pasivo_mas_resultado']):>14}")
    print()
    print(f"Cuadre: {'✓' if b['cuadra'] else '✗'}")
    return 0


def _cmd_pd_pyg_formateado(args) -> int:
    """PyG agrupada por grupos 6-7 del PGC."""
    from .partida_doble.presentacion import _GRUPOS_PYG
    repo = RepositorioAsiento('default')
    p = pyg_formateado(repo, desde=args.desde, hasta=args.hasta)

    print("CUENTA DE PÉRDIDAS Y GANANCIAS (agrupada por grupos PGC)")
    print("=" * 60)
    print()
    print("GASTOS (grupo 6)")
    print("-" * 60)
    if p["gastos"]:
        for c in sorted(p["gastos"].keys()):
            print(f"  {c:>8}  {_fmt_eur(p['gastos'][c]):>14}")
        print(f"  {'Total':>8}  {_fmt_eur(p['total_gastos']):>14}")
    else:
        print("  (sin gastos)")
    print()

    print("INGRESOS (grupo 7)")
    print("-" * 60)
    if p["ingresos"]:
        for c in sorted(p["ingresos"].keys()):
            print(f"  {c:>8}  {_fmt_eur(p['ingresos'][c]):>14}")
        print(f"  {'Total':>8}  {_fmt_eur(p['total_ingresos']):>14}")
    else:
        print("  (sin ingresos)")
    print()

    print("=" * 60)
    print(f"RESULTADO: {_fmt_eur(p['resultado']):>14}  "
          f"({'beneficio' if p['resultado'] >= 0 else 'pérdida'})")
    return 0


# ─── Parser ────────────────────────────────────────────────────

def registrar_subcomandos(sub) -> None:
    """Añade los subcomandos pd-* al parser existente."""
    p = sub.add_parser("pd-acto", help="Actos de partida doble (catálogo)")
    sub_acto = p.add_subparsers(dest="pd_acto_cmd", required=True)

    p_l = sub_acto.add_parser("listar", help="Lista los actos del catálogo")
    p_l.add_argument("--grupo", help="Filtra por grupo")
    p_l.set_defaults(handler=_cmd_pd_acto_listar)

    p_c = sub_acto.add_parser("crear", help="Crea un asiento desde un código de acto")
    p_c.add_argument("codigo", help="Código del acto (ej. A_FACT_EMIT_SERV_NAC_SIN_RET)")
    p_c.add_argument("--json", required=True, help="Parámetros en JSON")
    p_c.set_defaults(handler=_cmd_pd_acto_crear)

    p_d = sub.add_parser("pd-diario", help="Libro diario")
    p_d.add_argument("--desde", type=int)
    p_d.add_argument("--hasta", type=int)
    p_d.set_defaults(handler=_cmd_pd_diario)

    p_m = sub.add_parser("pd-mayor", help="Libro mayor")
    p_m.add_argument("--cuenta")
    p_m.add_argument("--desde", type=int)
    p_m.add_argument("--hasta", type=int)
    p_m.set_defaults(handler=_cmd_pd_mayor)

    p_b = sub.add_parser("pd-balance", help="Balance de comprobación")
    p_b.add_argument("--desde", type=int)
    p_b.add_argument("--hasta", type=int)
    p_b.set_defaults(handler=_cmd_pd_balance)

    p_p = sub.add_parser("pd-pyg", help="Cuenta de pérdidas y ganancias")
    p_p.add_argument("--desde", type=int)
    p_p.add_argument("--hasta", type=int)
    p_p.set_defaults(handler=_cmd_pd_pyg)

    p_s = sub.add_parser("pd-situacion", help="Balance de situación")
    p_s.add_argument("--desde", type=int)
    p_s.add_argument("--hasta", type=int)
    p_s.set_defaults(handler=_cmd_pd_situacion)
    p_bf = sub.add_parser("pd-balance-formateado",
        help="Balance agrupado por grupos PGC")
    p_bf.add_argument("--desde", type=int)
    p_bf.add_argument("--hasta", type=int)
    p_bf.set_defaults(handler=_cmd_pd_balance_formateado)

    p_pf = sub.add_parser("pd-pyg-formateado",
        help="PyG agrupada por grupos PGC")
    p_pf.add_argument("--desde", type=int)
    p_pf.add_argument("--hasta", type=int)
    p_pf.set_defaults(handler=_cmd_pd_pyg_formateado)

    p_v = sub.add_parser("pd-verificar", help="Verifica la cadena de asientos")
    p_v.add_argument("--desde", type=int)
    p_v.add_argument("--hasta", type=int)
    p_v.set_defaults(handler=_cmd_pd_verificar)

    p_r = sub.add_parser("pd-reset", help="Retirado: los asientos se corrigen por reversión")
    p_r.add_argument("--yes", action="store_true", help="Confirmar borrado")
    p_r.set_defaults(handler=_cmd_pd_reset)
