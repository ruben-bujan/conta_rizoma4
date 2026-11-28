#!/usr/bin/env python3
"""Aplica migrations/NNN_*.sql en orden. Idempotente: registra en _migrations."""
from __future__ import annotations
import os, sys
from pathlib import Path
import psycopg

MIG_DIR = Path(__file__).resolve().parent.parent / "migrations"

def main() -> int:
    url = os.environ.get("CONTA_PG_URL")
    if not url:
        print("ERROR: falta CONTA_PG_URL", file=sys.stderr); return 1
    archivos = sorted(MIG_DIR.glob("[0-9][0-9][0-9]_*.sql"))
    if not archivos:
        print("No hay migraciones."); return 0
    with psycopg.connect(url) as conn, conn.cursor() as cur:
        cur.execute("""CREATE TABLE IF NOT EXISTS _migrations (
            id text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())""")
        for f in archivos:
            cur.execute("SELECT 1 FROM _migrations WHERE id=%s", (f.name,))
            if cur.fetchone():
                print(f"   ✓ {f.name} (ya aplicada)"); continue
            print(f"   ▶ {f.name}")
            cur.execute(f.read_text(encoding="utf-8"))
            cur.execute("INSERT INTO _migrations (id) VALUES (%s)", (f.name,))
        conn.commit()
    print("✅ Migraciones al día.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
    