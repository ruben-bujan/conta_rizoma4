"""Pruebas mínimas del expediente piloto INCIVSA."""


def test_expediente_identifica_empresa_historica():
    from .inventario import EMPRESA_HEREDADA, analizar_csv

    resultado = analizar_csv()

    assert EMPRESA_HEREDADA == "INCIV_2010"
    assert resultado["empresa_historica"] == "INCIV_2010"


def test_csv_piloto_puede_inventariarse():
    from .inventario import analizar_csv

    resultado = analizar_csv()

    assert "error" not in resultado
    assert resultado["grupos_brutos"] > 0
    assert resultado["filas_validas"] > 0


def test_identidad_fiscal_extraordinaria_esta_documentada():
    from pathlib import Path

    texto = Path("pilot_incivsa/expediente.md").read_text(encoding="utf-8")

    assert "INCIV, _2010" in texto
    assert "S/80866700-A80866700" in texto
    assert "actuaciones judiciales y administrativas extraordinarias" in texto


def test_importador_no_se_recomienda_sin_revision():
    from pathlib import Path

    ruta = Path("scripts/importar_inciv_2010.py")
    texto = ruta.read_text(encoding="utf-8")

    assert "_limpiar()" in texto
    assert 'DELETE FROM asiento_contable' in texto
