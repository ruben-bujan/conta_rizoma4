# -*- coding: utf-8 -*-
from datetime import date
import psycopg
import pytest
from conta_rizoma4.partida_doble import (
    RepositorioAsiento, BackendPostgres,
    crear_asiento, guardar_asiento, borrar_asiento, Linea,
    get_backend,
)
from conta_rizoma4.partida_doble.persistencia import PG_URL
from conta_rizoma4.operativo.asiento import GENESIS
from conta_rizoma4.config import ConfigError, get_config, get_empresa


EMPRESAS_TEST = ['TEST_EMP_A', 'TEST_EMP_B']


def _limpiar():
    with psycopg.connect(PG_URL) as conn:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM linea_asiento WHERE empresa_id = ANY(%s)', (EMPRESAS_TEST,))
            cur.execute('DELETE FROM asiento_contable WHERE empresa_id = ANY(%s)', (EMPRESAS_TEST,))
        conn.commit()


@pytest.fixture
def empresas_limpias():
    _limpiar()
    yield
    _limpiar()


class TestAislamiento:
    def test_empresa_id_obligatorio(self):
        with pytest.raises(ValueError, match='empresa_id es obligatorio'):
            RepositorioAsiento('')
        with pytest.raises(ValueError, match='empresa_id es obligatorio'):
            RepositorioAsiento('   ')

    def test_guardar_aisla_por_empresa(self, empresas_limpias):
        for empresa, n in [('TEST_EMP_A', 2), ('TEST_EMP_B', 1)]:
            for i in range(n):
                a = crear_asiento(
                    indice=i, fecha=date(2025, 1, 1),
                    concepto=f'{empresa}-{i}',
                    lineas=[
                        Linea('572', debe_centimos=100_000),
                        Linea('100', haber_centimos=100_000),
                    ],
                    hash_previo=GENESIS,
                )
                guardar_asiento(a, empresa_id=empresa)
        repo_a = RepositorioAsiento('TEST_EMP_A')
        repo_b = RepositorioAsiento('TEST_EMP_B')
        assert repo_a.contar() == 2
        assert repo_b.contar() == 1

    def test_obtener_no_ve_otra_empresa(self, empresas_limpias):
        a = crear_asiento(indice=0, fecha=date(2025, 1, 1), concepto='X', lineas=[Linea('572', debe_centimos=100_000), Linea('100', haber_centimos=100_000)], hash_previo=GENESIS)
        guardar_asiento(a, empresa_id='TEST_EMP_A')
        assert RepositorioAsiento('TEST_EMP_A').obtener(0) is not None
        assert RepositorioAsiento('TEST_EMP_B').obtener(0) is None

    def test_verificar_cadena_aislada(self, empresas_limpias):
        a = crear_asiento(indice=0, fecha=date(2025, 1, 1), concepto='X', lineas=[Linea('572', debe_centimos=100_000), Linea('100', haber_centimos=100_000)], hash_previo=GENESIS)
        guardar_asiento(a, empresa_id='TEST_EMP_A')
        rep_a = RepositorioAsiento('TEST_EMP_A').verificar_cadena()
        rep_b = RepositorioAsiento('TEST_EMP_B').verificar_cadena()
        assert rep_a.total == 1 and rep_a.cadena_valida
        assert rep_b.total == 0 and rep_b.cadena_valida

    def test_borrado_fisico_deshabilitado(self, empresas_limpias):
        a = crear_asiento(indice=0, fecha=date(2025, 1, 1), concepto='X', lineas=[Linea('572', debe_centimos=100_000), Linea('100', haber_centimos=100_000)], hash_previo=GENESIS)
        guardar_asiento(a, empresa_id='TEST_EMP_A')
        with pytest.raises(RuntimeError, match='deshabilitado'):
            borrar_asiento(0, empresa_id='TEST_EMP_B')
        assert RepositorioAsiento('TEST_EMP_A').obtener(0) is not None


class TestBackend:
    def test_get_backend_postgres(self, monkeypatch):
        monkeypatch.setenv('CONTA_BACKEND', 'postgres')
        b = get_backend()
        assert isinstance(b, BackendPostgres)

    def test_get_backend_http_sin_url_falla(self, monkeypatch):
        monkeypatch.setenv('CONTA_BACKEND', 'http')
        monkeypatch.delenv('CONTA_HTTP_URL', raising=False)
        with pytest.raises(ValueError, match='CONTA_HTTP_URL'):
            get_backend()

    def test_get_backend_desconocido(self, monkeypatch):
        monkeypatch.setenv('CONTA_BACKEND', 'xyz')
        with pytest.raises(ValueError, match='desconocido'):
            get_backend()


class TestConfigYTenant:
    def test_default_esta_en_config(self):
        assert 'default' in get_config().empresas

    def test_empresa_inexistente_falla(self):
        with pytest.raises(ConfigError, match='no está en config'):
            get_empresa('NO_EXISTE')
