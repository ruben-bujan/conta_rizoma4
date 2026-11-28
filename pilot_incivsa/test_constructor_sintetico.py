"""Pruebas aisladas del constructor con fixtures sintéticos, sin abrir el CSV del piloto."""
import csv

import pytest

from pilot_incivsa.constructor_memoria import _parse_importe, construir_desde_csv


def _fila(codigo, fecha, concepto, cuenta, debe, haber):
    fila = [""] * 13
    fila[5] = codigo
    fila[6] = fecha
    fila[7] = concepto
    fila[8] = cuenta
    fila[11] = debe
    fila[12] = haber
    return fila


def _escribir(ruta, filas):
    with ruta.open("w", encoding="latin-1", newline="") as fichero:
        escritor = csv.writer(fichero)
        escritor.writerow([f"columna_{i}" for i in range(13)])
        escritor.writerows(filas)
    return ruta


def test_parse_importe_es_exacto_y_rechaza_fracciones_de_centimo():
    assert _parse_importe("1,234.56") == 123456
    with pytest.raises(ValueError, match="dos decimales"):
        _parse_importe("1.005")
    with pytest.raises(ValueError, match="no finito"):
        _parse_importe("NaN")


def test_constructor_sintetico_conserva_cuadre_sin_float(tmp_path):
    ruta = _escribir(tmp_path / "sintetico.csv", [
        _fila("A-1", "2025-01-03", "Compra", "600", "12.34", ""),
        _fila("A-1", "2025-01-03", "Compra", "400", "", "12.34"),
    ])

    resultado = construir_desde_csv(ruta)

    assert resultado.grupos_totales == 1
    assert resultado.grupos_cuadrados == 1
    assert resultado.asientos[0].cuadra
    assert resultado.asientos[0].lineas[0].debe_centimos == 1234
    assert len(resultado.grupos_origen) == 1
    assert resultado.grupos_origen[0].estado_migracion == "CANDIDATO_CUADRADO"
    assert len(resultado.grupos_origen[0].filas_originales) == 2


def test_constructor_sintetico_clasifica_importe_invalido_y_no_crea_asiento(tmp_path):
    ruta = _escribir(tmp_path / "invalido.csv", [
        _fila("A-2", "2025-01-03", "Compra", "600", "1.005", ""),
        _fila("A-2", "2025-01-03", "Compra", "400", "", "1.005"),
    ])

    resultado = construir_desde_csv(ruta)

    assert resultado.asientos == []
    assert resultado.grupos_descuadrados == 1
    assert resultado.errores_origen[0]["tipo"] == "LINEA_ORIGEN_INVALIDA"
    assert resultado.grupos_origen[0].estado_migracion == "NO_DETERMINADO_PRECISION_O_LINEA"
    assert len(resultado.grupos_origen[0].filas_originales) == 2
