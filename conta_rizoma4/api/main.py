# -*- coding: utf-8 -*-
"""API HTTP de conta-rizoma4.

Expone los endpoints que rizoma4 (o cualquier cliente) necesita para
leer/escribir asientos y verificar la cadena hash.

Arranque:
    uvicorn conta_rizoma4.api.main:app --port 8001

Endpoints:
    GET  /health                        — health check
    GET  /empresas                      — listado de empresas (de la config)
    GET  /empresas/{empresa_id}         — detalle de una empresa
    GET  /asientos?empresa_id=...       — listado de asientos
    GET  /asientos/{indice}?empresa_id= — obtener un asiento
    POST /asientos                      — crear asiento (desde acto)
    POST /verificar                     — verificar cadena hash
"""
from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from ..config import get_config
from .routers import asientos, empresas, verificar, leases, obras, operarios, documentos, auth, corpus_forense, configuracion as config


app = FastAPI(
    title="conta-rizoma4 API",
    description=(
        "API de contabilidad doctrinal sobre el PGC. "
        "115 actos, partida doble, hash chain."
    ),
    version="0.9.0",
)

# El frontend servido por esta misma API no requiere CORS. Los clientes
# externos deben declarar orígenes concretos; no hay comodín por defecto.
_cors_origins = [
    origen.strip()
    for origen in os.environ.get("CONTA_API_CORS_ORIGINS", "").split(",")
    if origen.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(asientos.router)
app.include_router(verificar.router)
app.include_router(empresas.router)
app.include_router(auth.router)
app.include_router(corpus_forense.router)
app.include_router(leases.router)
app.include_router(obras.router)
app.include_router(operarios.router)
app.include_router(documentos.router)
app.include_router(config.router)


# Servir el frontend estático
_frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
_frontend_dir = os.path.abspath(_frontend_dir)
if os.path.isdir(_frontend_dir):
    app.mount("/frontend", StaticFiles(directory=_frontend_dir), name="frontend")


@app.get("/")
def raiz():
    """Redirige al frontend."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/frontend/index.html")


@app.get("/health")
def health() -> dict:
    cfg = get_config()
    return {
        "status": "ok",
        "empresas_configuradas": len(cfg.empresas),
        "moneda_grupo": cfg.moneda_grupo,
        "marco_default": cfg.marco_contable_default,
    }
