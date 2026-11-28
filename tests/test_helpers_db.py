"""Limpieza física permitida solo dentro de fixtures de pruebas."""
import psycopg

from conta_rizoma4.partida_doble.persistencia import PG_URL


def limpiar_asiento_prueba(indice: int, empresa_id: str = "default") -> None:
    with psycopg.connect(PG_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM linea_asiento WHERE empresa_id = %s AND asiento_indice = %s",
                (empresa_id, indice),
            )
            cur.execute(
                "DELETE FROM asiento_contable WHERE empresa_id = %s AND indice = %s",
                (empresa_id, indice),
            )
