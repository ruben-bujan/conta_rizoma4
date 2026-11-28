"""Backup CSV de tablas pgc_* antes de operaciones destructivas."""
from __future__ import annotations
from datetime import datetime
from pathlib import Path

import psycopg

TABLES = ("pgc_cuenta", "pgc_texto", "pgc_jerarquia", "pgc_jerarquia_relacion")


def backup_tablas(conn: psycopg.Connection, out_dir: Path) -> list[Path]:
    """Volca cada tabla existente a un CSV. Devuelve los ficheros creados."""
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    creados: list[Path] = []
    with conn.cursor() as cur:
        for t in TABLES:
            cur.execute("SELECT to_regclass(%s)", (f"public.{t}",))
            if cur.fetchone()[0] is None:
                continue
            out = out_dir / f"{t}_{ts}.csv"
            with cur.copy(f"COPY {t} TO STDOUT WITH CSV HEADER") as copy, \
                 out.open("wb") as f:
                for chunk in copy:
                    f.write(chunk)
            creados.append(out)
            print(f"   💾 {t} → {out}")
    return creados