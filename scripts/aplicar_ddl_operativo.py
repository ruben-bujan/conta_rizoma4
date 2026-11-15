#!/usr/bin/env python3
"""Aplica el DDL operativo (acto_economico + justificacion_interna)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg


PG_URL = os.environ.get(
    "CONTA_PG_URL",
    "postgresql://rizoma:rizoma_dev@localhost:5433/conta_rizoma4",
)


def main() -> int:
    ddl_path = Path(__file__).parent / "ddl_operativo.sql"
    ddl = ddl_path.read_text(encoding="utf-8")
    with psycopg.connect(PG_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(ddl)
        conn.commit()
    print(f"DDL aplicado en {PG_URL}")
    return 0


if __name__ == "__main__":
    sys.exit(main())