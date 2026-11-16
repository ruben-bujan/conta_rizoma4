#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Worker de limpieza: marca como EXPIRADO los leases caducados.

Uso:
    python scripts/worker_leases.py          # una vez
    python scripts/worker_leases.py --loop   # cada 60s
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from conta_rizoma4.custodia.repositorios import RepositorioLease


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--loop", action="store_true", help="Ejecutar cada 60s")
    parser.add_argument("--interval", type=int, default=60, help="Segundos entre ejecuciones")
    args = parser.parse_args()

    repo = RepositorioLease()

    def _una_vez():
        n = repo.expirar_antiguos()
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Leases expirados: {n}")

    if args.loop:
        print(f"Worker en bucle (cada {args.interval}s). Ctrl+C para salir.")
        try:
            while True:
                _una_vez()
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nWorker detenido.")
            return 0
    else:
        _una_vez()
        return 0


if __name__ == "__main__":
    sys.exit(main())
