"""Compatibilidad entre la POC y el dominio formal promovido."""


def test_linea_poc_a_dominio():
    from poc_epistemico_contable.modelo import Linea as LineaPOC
    from conta_rizoma4.dominio.compatibilidad_poc import linea_poc_a_dominio

    linea = linea_poc_a_dominio(LineaPOC("430", debe=121000))

    assert linea.cuenta == "430"
    assert linea.debe == 121000


def test_linea_dominio_a_poc():
    from conta_rizoma4.dominio import Linea
    from conta_rizoma4.dominio.compatibilidad_poc import linea_dominio_a_poc

    linea = linea_dominio_a_poc(Linea("705", haber=121000))

    assert linea.cuenta == "705"
    assert linea.haber == 121000
