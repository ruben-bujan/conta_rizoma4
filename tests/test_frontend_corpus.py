# -*- coding: utf-8 -*-
"""Tests del frontend de corpus."""
from fastapi.testclient import TestClient
from conta_rizoma4.api.main import app


client = TestClient(app)


class TestFrontendCorpus:
    def test_corpus_html(self):
        r = client.get("/frontend/corpus.html")
        assert r.status_code == 200
        assert "Corpus forense" in r.text
        assert "cargarAgregado" in r.text

    def test_corpus_js(self):
        r = client.get("/frontend/corpus.js")
        assert r.status_code == 200
        assert "cargarAgregado" in r.text
        assert "cargarPatrones" in r.text

    def test_corpus_endpoint_agregado(self):
        r = client.get("/corpus/agregado")
        assert r.status_code == 200
        assert "totales" in r.json()

    def test_corpus_endpoint_patrones(self):
        r = client.get("/corpus/patrones")
        assert r.status_code == 200
        assert "alertas" in r.json()
