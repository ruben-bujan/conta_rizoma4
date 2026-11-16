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
    DELETE /asientos/{indice}?empresa_id= — borrar asiento
    POST /verificar                     — verificar cadena hash
"""
from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..config import get_config
from .routers import asientos, empresas, verificar, leases, obras, operarios, documentos


app = FastAPI(
    title="conta-rizoma4 API",
    description=(
        "API de contabilidad doctrinal sobre el PGC. "
        "115 actos, partida doble, hash chain."
    ),
    version="0.9.0",
)

# CORS (para que rizoma4 o el frontend puedan consumir la API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CONTA_API_CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(asientos.router)
app.include_router(verificar.router)
app.include_router(empresas.router)
app.include_router(leases.router)
app.include_router(obras.router)
app.include_router(operarios.router)
app.include_router(documentos.router)


@app.get("/health")
def health() -> dict:
    cfg = get_config()
    return {
        "status": "ok",
        "empresas_configuradas": len(cfg.empresas),
        "moneda_grupo": cfg.moneda_grupo,
        "marco_default": cfg.marco_contable_default,
    }
