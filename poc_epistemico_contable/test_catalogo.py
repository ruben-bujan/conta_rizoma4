"""Pruebas de clasificación del catálogo sin importar módulos heredados."""
from .catalogo import cargar_catalogo, resumen_catalogo


def test_catalogo_visible_y_clasificado():
    catalogo = cargar_catalogo()
    assert len(catalogo) >= 115
    assert all(item.codigo.startswith("A_") for item in catalogo)
    assert all(item.responsabilidad for item in catalogo)


def test_acto_informativo_no_se_clasifica_como_asiento():
    catalogo = cargar_catalogo()
    por_codigo = {item.codigo: item for item in catalogo}
    assert "A_MODELO_347" in por_codigo
    assert por_codigo["A_MODELO_347"].responsabilidad == "OBLIGACION_DECLARATIVA"
    assert not por_codigo["A_MODELO_347"].genera_asiento


def test_reclasificacion_se_identifica_por_responsabilidad():
    catalogo = cargar_catalogo()
    por_codigo = {item.codigo: item for item in catalogo}
    coincidencias = [
        item for item in catalogo
        if item.responsabilidad == "RECTIFICACION_O_RECLASIFICACION"
    ]
    assert coincidencias


def test_resumen_no_es_vacio():
    resumen = resumen_catalogo()
    assert sum(resumen.values()) >= 115
