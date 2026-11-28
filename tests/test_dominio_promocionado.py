"""Pruebas de promoción del dominio a contenedor estable."""


def test_api_publica_importa_entidades_sin_infraestructura():
    from conta_rizoma4.dominio import (
        Actor,
        Criterio,
        Evidencia,
        HechoEconomico,
        Linea,
        RepresentacionContable,
    )

    assert Actor.__name__ == "Actor"
    assert Criterio.__name__ == "Criterio"
    assert Evidencia.__name__ == "Evidencia"
    assert HechoEconomico.__name__ == "HechoEconomico"
    assert Linea.__name__ == "Linea"
    assert RepresentacionContable.__name__ == "RepresentacionContable"


def test_linea_nucleo_estable_rechaza_importes_invalidos():
    from conta_rizoma4.dominio import Linea

    try:
        Linea("430", debe=100, haber=100)
    except ValueError:
        return
    raise AssertionError("Una línea no puede contener debe y haber simultáneamente")


def test_puerto_repositorio_es_abierto_sin_postgres():
    from conta_rizoma4.dominio import RepositorioDominio

    assert getattr(RepositorioDominio, "__abstractmethods__", set())
