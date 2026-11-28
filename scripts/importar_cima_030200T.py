#!/usr/bin/env python3
"""Importador CIMA histórico retirado.

El flujo antiguo limpiaba físicamente la empresa y podía duplicar datos tras
fallos parciales. No se ejecuta hasta contar con un importador reversible,
idempotente y con lote de origen verificable.
"""
import sys


def main() -> int:
    print(
        "Importación CIMA deshabilitada: el flujo legado era destructivo. "
        "No se ha migrado información CIMA con este script.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
