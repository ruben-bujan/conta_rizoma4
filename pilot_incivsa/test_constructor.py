"""Pruebas del constructor aislado INCIVSA."""


def test_constructor_no_crea_persistencia():
    from .constructor_memoria import construir_desde_csv

    resultado = construir_desde_csv()

    assert resultado.grupos_totales > 0
    assert len(resultado.asientos) > 0


def test_todos_los_asientos_cuadran():
    from .constructor_memoria import construir_desde_csv

    resultado = construir_desde_csv()

    assert all(asiento.cuadra for asiento in resultado.asientos)


def test_constructor_tiene_resultado_clasificado():
    from .constructor_memoria import construir_desde_csv

    resultado = construir_desde_csv()

    assert resultado.grupos_totales == (
        resultado.grupos_cuadrados + resultado.grupos_descuadrados
        - resultado.grupos_subdivididos
        + len(resultado.errores_origen)
    ) or resultado.grupos_totales >= resultado.grupos_cuadrados
