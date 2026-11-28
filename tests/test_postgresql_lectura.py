"""Pruebas del adaptador PostgreSQL de sólo lectura."""


def test_sql_lectura_valida():
    from conta_rizoma4.dominio.adaptadores.postgresql_lectura import validar_sql_lectura

    assert "SELECT" in validar_sql_lectura("SELECT * FROM dominio_hecho").upper()


def test_sql_update_rechazado():
    from conta_rizoma4.dominio.adaptadores.postgresql_lectura import (
        EscrituraProhibidaError,
        validar_sql_lectura,
    )

    try:
        validar_sql_lectura("UPDATE dominio_hecho SET descripcion = 'x'")
    except EscrituraProhibidaError:
        return
    raise AssertionError("Debe rechazar UPDATE")


def test_sql_delete_rechazado():
    from conta_rizoma4.dominio.adaptadores.postgresql_lectura import (
        EscrituraProhibidaError,
        validar_sql_lectura,
    )

    try:
        validar_sql_lectura("DELETE FROM dominio_hecho")
    except EscrituraProhibidaError:
        return
    raise AssertionError("Debe rechazar DELETE")


def test_repositorio_sin_metodo_guardar():
    from conta_rizoma4.dominio.adaptadores.postgresql_lectura import RepositorioPostgresLectura

    repositorio = RepositorioPostgresLectura(pg_url="postgresql://usuario@localhost/base")

    assert not hasattr(repositorio, "guardar")
    assert not hasattr(repositorio, "guardar_asiento")


def test_select_abre_transaccion_postgres_solo_lectura(monkeypatch):
    import psycopg
    from conta_rizoma4.dominio.adaptadores.postgresql_lectura import RepositorioPostgresLectura

    llamadas = []

    class Cursor:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def execute(self, sql, parametros):
            llamadas.append((sql.strip(), parametros))
        def fetchall(self):
            return []

    class Connection:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def transaction(self):
            return self
        def cursor(self):
            return Cursor()
        def execute(self, sql):
            llamadas.append((sql.strip(), ()))
    monkeypatch.setattr(psycopg, "connect", lambda *args, **kwargs: Connection())
    repo = RepositorioPostgresLectura("postgresql://test/test")
    assert repo._ejecutar_select("SELECT 1") == []
    assert llamadas[0][0] == "SET TRANSACTION READ ONLY"
