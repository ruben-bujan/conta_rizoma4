#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extrae todo el contenido de un fichero .mdb (Access) a CSV/JSON.

Uso:
    python scripts/extraer_mdb.py /ruta/al/fichero.mdb [--out /ruta/salida]

Produce:
    <out>/<tabla>.csv       — cada tabla en CSV
    <out>/<tabla>.json      — cada tabla en JSON
    <out>/_schema.json      — esquema de todas las tablas
    <out>/_resumen.txt      — resumen legible

Requiere: mdbtools (mdb-tables, mdb-schema, mdb-export).
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str]) -> str:
    """Ejecuta un comando y devuelve stdout. Falla si hay error."""
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"Error ejecutando {' '.join(cmd)}: {r.stderr}")
    return r.stdout


def listar_tablas(mdb: Path) -> list[str]:
    """Lista las tablas del MDB."""
    out = _run(["mdb-tables", "-1", str(mdb)])
    return [t.strip() for t in out.splitlines() if t.strip()]


def exportar_tabla_csv(mdb: Path, tabla: str, out_csv: Path) -> int:
    """Exporta una tabla a CSV. Devuelve el número de filas."""
    out = _run(["mdb-export", str(mdb), tabla])
    out_csv.write_text(out, encoding="utf-8")
    # Contar filas (sin cabecera)
    n = max(0, len(out.splitlines()) - 1)
    return n


def exportar_tabla_json(mdb: Path, tabla: str, out_json: Path) -> int:
    """Exporta una tabla a JSON (lista de dicts). Devuelve el número de filas."""
    out = _run(["mdb-export", "-b", "hex", str(mdb), tabla])
    # Parsear CSV
    reader = csv.DictReader(out.splitlines())
    rows = [dict(r) for r in reader]
    out_json.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return len(rows)


def exportar_esquema(mdb: Path, out_schema: Path) -> str:
    """Exporta el esquema completo (CREATE TABLE ...) a un fichero."""
    out = _run(["mdb-schema", str(mdb)])
    out_schema.write_text(out, encoding="utf-8")
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mdb", type=Path, help="Ruta al fichero .mdb")
    parser.add_argument(
        "--out", type=Path, default=None,
        help="Directorio de salida (default: ./mdb_extraido_<nombre>)",
    )
    parser.add_argument(
        "--no-json", action="store_true", help="No generar JSON"
    )
    args = parser.parse_args()

    if not args.mdb.exists():
        print(f"ERROR: no existe {args.mdb}", file=sys.stderr)
        return 1
    if args.mdb.suffix.lower() not in (".mdb", ".accdb"):
        print(f"AVISO: extensión {args.mdb.suffix} no es .mdb", file=sys.stderr)

    out_dir = args.out or Path(f"mdb_extraido_{args.mdb.stem}")
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"MDB:  {args.mdb}")
    print(f"Out:  {out_dir.resolve()}")
    print()

    # 1. Listar tablas
    try:
        tablas = listar_tablas(args.mdb)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print(f"Tablas encontradas: {len(tablas)}")
    for t in tablas:
        print(f"  - {t}")
    print()

    # 2. Esquema
    try:
        esquema = exportar_esquema(args.mdb, out_dir / "_schema.sql")
        print(f"Esquema:  {len(esquema.splitlines())} líneas -> _schema.sql")
    except RuntimeError as e:
        print(f"AVISO: no se pudo exportar el esquema: {e}", file=sys.stderr)

    # 3. Cada tabla a CSV (+ JSON)
    resumen = []
    for t in tablas:
        try:
            n = exportar_tabla_csv(args.mdb, t, out_dir / f"{t}.csv")
            resumen.append({"tabla": t, "filas": n})
            print(f"  {t}: {n} filas -> {t}.csv")
            if not args.no_json:
                exportar_tabla_json(args.mdb, t, out_dir / f"{t}.json")
        except RuntimeError as e:
            print(f"  {t}: ERROR — {e}", file=sys.stderr)

    # 4. Resumen
    resumen_path = out_dir / "_resumen.txt"
    with resumen_path.open("w", encoding="utf-8") as f:
        f.write(f"MDB: {args.mdb}\n")
        f.write(f"Tablas: {len(tablas)}\n\n")
        for r in resumen:
            f.write(f"{r['tabla']}: {r['filas']} filas\n")
    print()
    print(f"Resumen: {resumen_path}")

    print()
    print("Hecho.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
