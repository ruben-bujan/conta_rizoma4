# -*- coding: utf-8 -*-
"""Pruebas de contrato HTTP del cliente CONTA → RIZOMA4."""
from __future__ import annotations

from conta_rizoma4.api import rizoma4_client
from conta_rizoma4.api.rizoma4_client import ClienteRizoma4, Rizoma4Error


class RespuestaFalsa:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status
        self.text = "respuesta simulada"

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError(self.text)

    def json(self):
        return self._payload


def test_listar_casos_usa_catalogo_y_token(monkeypatch):
    capturado = {}

    def get(url, headers, timeout):
        capturado.update(url=url, headers=headers, timeout=timeout)
        return RespuestaFalsa({"total": 1, "casos": [{"caso_id": "CASO_1"}]})

    monkeypatch.setattr(rizoma4_client.requests, "get", get)
    cliente = ClienteRizoma4(base_url="http://rizoma.test", token="token-prueba")
    assert cliente.listar_casos() == [{"caso_id": "CASO_1"}]
    assert capturado["url"] == "http://rizoma.test/casos"
    assert capturado["headers"]["Authorization"] == "Bearer token-prueba"


def test_listar_casos_falla_con_error_http(monkeypatch):
    def get(*args, **kwargs):
        return RespuestaFalsa({}, status=503)

    monkeypatch.setattr(rizoma4_client.requests, "get", get)
    try:
        ClienteRizoma4().listar_casos()
    except Rizoma4Error:
        pass
    else:
        raise AssertionError("Se esperaba Rizoma4Error")


def test_subida_directa_cas_usa_contrato_de_conta(monkeypatch):
    capturado = {}

    def post(url, headers, data, files, timeout):
        capturado.update(url=url, data=data, files=files, headers=headers)
        return RespuestaFalsa({"hash_cas": "a" * 64})

    monkeypatch.setattr(rizoma4_client.requests, "post", post)
    cliente = ClienteRizoma4(base_url="http://rizoma.test")
    resultado = cliente.guardar_documento(
        empresa_id="EMPRESA_1", contenido=b"documento", nombre="factura.pdf",
    )
    assert resultado["hash_cas"] == "a" * 64
    assert capturado["url"] == "http://rizoma.test/cas/subir"
    assert capturado["data"] == {"empresa_id": "EMPRESA_1", "nombre": "factura.pdf"}
    assert "contenido" in capturado["files"]
