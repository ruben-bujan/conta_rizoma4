#!/usr/bin/env python3
"""Concede o revoca delegaciones contables en `dominio_evento` desde consola local."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from conta_rizoma4.dominio.adaptadores.repositorio_postgres import RepositorioPermisosEvento


def _fecha(valor: str | None) -> datetime | None:
    if not valor:
        return None
    return datetime.fromisoformat(valor)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subcomandos = parser.add_subparsers(dest="accion", required=True)

    conceder = subcomandos.add_parser("conceder")
    conceder.add_argument("--empresa-id", required=True)
    conceder.add_argument("--permiso-id", required=True)
    conceder.add_argument("--otorgante-id", required=True)
    conceder.add_argument("--otorgante-rol", required=True)
    conceder.add_argument("--beneficiario-id", required=True)
    conceder.add_argument("--beneficiario-rol", required=True)
    conceder.add_argument("--competencia", required=True)
    conceder.add_argument("--alcance")
    conceder.add_argument("--vigente-hasta")
    conceder.add_argument("--confirmar", action="store_true")

    revocar = subcomandos.add_parser("revocar")
    revocar.add_argument("--empresa-id", required=True)
    revocar.add_argument("--permiso-id", required=True)
    revocar.add_argument("--actor-id", required=True)
    revocar.add_argument("--motivo", required=True)
    revocar.add_argument("--confirmar", action="store_true")

    args = parser.parse_args()
    if not args.confirmar:
        parser.error("Añade --confirmar para escribir en el ledger de dominio")

    repositorio = RepositorioPermisosEvento()
    momento = datetime.now(timezone.utc)
    if args.accion == "conceder":
        repositorio.conceder(
            entidad_id=args.empresa_id,
            permiso_id=args.permiso_id,
            otorgante_id=args.otorgante_id,
            otorgante_rol=args.otorgante_rol,
            beneficiario_id=args.beneficiario_id,
            beneficiario_rol=args.beneficiario_rol,
            competencia=args.competencia,
            alcance=args.alcance or args.empresa_id,
            otorgada_en=momento,
            vigente_hasta=_fecha(args.vigente_hasta),
        )
        print("Permiso concedido en dominio_evento.")
        return 0

    repositorio.revocar(
        entidad_id=args.empresa_id,
        permiso_id=args.permiso_id,
        actor_id=args.actor_id,
        motivo=args.motivo,
        revocada_en=momento,
    )
    print("Permiso revocado en dominio_evento.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
