"""Configuración PostgreSQL central de CONTA-RIZOMA4.

No contiene credenciales predeterminadas.
La configuración ausente o incompleta produce un error explícito.
"""

import os

from psycopg.conninfo import make_conninfo


def _obligatoria(nombre: str) -> str:
    valor = os.environ.get(nombre)

    if valor is None or not valor.strip():
        raise RuntimeError(
            f"Configuración PostgreSQL incompleta: falta {nombre}"
        )

    return valor.strip()


def _configuracion() -> dict:
    host = _obligatoria("CONTA_PG_HOST")
    port_text = _obligatoria("CONTA_PG_PORT")
    dbname = _obligatoria("CONTA_PG_DB")
    user = _obligatoria("CONTA_PG_USER")
    password = _obligatoria("CONTA_PG_PASSWORD")

    try:
        port = int(port_text)
    except ValueError as exc:
        raise RuntimeError(
            "CONTA_PG_PORT debe ser numérico"
        ) from exc

    if not 1 <= port <= 65535:
        raise RuntimeError(
            "CONTA_PG_PORT está fuera del rango válido"
        )

    try:
        timeout = int(
            os.environ.get("CONTA_PG_CONNECT_TIMEOUT", "10")
        )
    except ValueError as exc:
        raise RuntimeError(
            "CONTA_PG_CONNECT_TIMEOUT debe ser numérico"
        ) from exc

    if timeout < 1:
        raise RuntimeError(
            "CONTA_PG_CONNECT_TIMEOUT debe ser positivo"
        )

    return {
        "host": host,
        "port": port,
        "dbname": dbname,
        "user": user,
        "password": password,
        "connect_timeout": timeout,
        "application_name": "CONTA-RIZOMA4",
    }


_url_env = os.environ.get("CONTA_PG_URL", "").strip()
if _url_env:
    PG_URL = _url_env
else:
    PG_URL = make_conninfo(**_configuracion())
