"""Pruebas conceptuales del contrato de escritura PostgreSQL."""


def test_diseno_no_contiene_sql():
    from pathlib import Path

    ruta = Path("conta_rizoma4/dominio/adaptadores/postgresql_escritura_diseno.py")
    texto = ruta.read_text(encoding="utf-8")

    assert "psycopg" not in texto
    assert "INSERT" not in texto
    assert "UPDATE" not in texto
    assert "DELETE" not in texto


def test_operacion_escritura_registra_referencias():
    from datetime import datetime
    from conta_rizoma4.dominio.adaptadores.postgresql_escritura_diseno import OperacionEscritura

    operacion = OperacionEscritura(
        tipo="HECHO_REGISTRADO",
        entidad_id="EMP-A",
        objeto_id="H-1",
        payload={"tipo": "EJECUCION_SERVICIO"},
        actor_id="CONTADOR",
        motivo="Alta",
        timestamp=datetime(2025, 4, 18),
    )

    assert operacion.entidad_id == "EMP-A"
    assert operacion.objeto_id == "H-1"


def test_ddl_partida_doble_no_contiene_anotacion_python_en_sql():
    from pathlib import Path

    texto = Path("scripts/ddl_partida_doble.sql").read_text(encoding="utf-8")
    assert "parrafo_pgc_id INTEGER NULL" in texto
    assert "parrafo_pgc_id:" not in texto


def test_listado_ordinario_excluye_importaciones_pendientes_por_defecto():
    from pathlib import Path

    texto = Path("conta_rizoma4/partida_doble/repositorio.py").read_text(encoding="utf-8")
    assert "incluir_importaciones_pendientes: bool = False" in texto
    assert "COALESCE(metadatos->>'lote_importacion', '') = ''" in texto
