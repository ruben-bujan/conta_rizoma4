from conta_rizoma4.dominio.adaptadores.incivsa_lectura import RepositorioINCIVSALectura


def test_lectura_incivsa_pagina_y_filtro_estado(monkeypatch):
    consultas = []

    def select(self, sql, parametros=()):
        consultas.append((" ".join(sql.split()), parametros))
        return []

    monkeypatch.setattr(
        "conta_rizoma4.dominio.adaptadores.postgresql_lectura.RepositorioPostgresLectura._ejecutar_select",
        select,
    )
    repo = RepositorioINCIVSALectura("postgresql://solo-lectura")
    assert repo.listar_lotes("INCIV_2010", 25) == []
    assert repo.listar_grupos(
        "INCIV_2010", "a" * 64,
        estado="NO_DETERMINADO_DESCUADRE", limite=10, desplazamiento=20,
    ) == []
    assert consultas[0][1] == ("INCIV_2010", 25)
    assert consultas[1][1] == (
        "INCIV_2010", "a" * 64, "NO_DETERMINADO_DESCUADRE", 10, 20,
    )
    assert "DELETE" not in consultas[0][0]


def test_lectura_incivsa_rechaza_paginacion_fuera_de_rango():
    import pytest

    repo = RepositorioINCIVSALectura("postgresql://solo-lectura")
    with pytest.raises(ValueError, match="paginación"):
        repo.listar_grupos("INCIV_2010", "a" * 64, limite=201)
