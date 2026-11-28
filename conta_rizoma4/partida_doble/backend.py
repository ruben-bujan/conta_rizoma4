# -*- coding: utf-8 -*-
from __future__ import annotations
import os
from abc import ABC, abstractmethod
from datetime import date
from typing import Optional
from .modelo import Asiento, Linea
from .persistencia import guardar_asiento, revertir_asiento
from .repositorio import RepositorioAsiento, ReporteCadenaAsientos
from .creacion import crear_asiento
from ..operativo.asiento import GENESIS


class BackendContable(ABC):
    @abstractmethod
    def obtener(self, empresa_id, indice): ...
    @abstractmethod
    def listar(self, empresa_id, **kwargs): ...
    @abstractmethod
    def crear_siguiente(self, empresa_id, **kwargs): ...
    @abstractmethod
    def verificar_cadena(self, empresa_id, **kwargs): ...
    @abstractmethod
    def borrar(self, empresa_id, indice, motivo="Anulación vía backend", actor="backend"): ...


class BackendPostgres(BackendContable):
    def __init__(self, pg_url=None):
        self._pg_url = pg_url
    def obtener(self, empresa_id, indice):
        return RepositorioAsiento(empresa_id, self._pg_url).obtener(indice)
    def listar(self, empresa_id, **kwargs):
        return RepositorioAsiento(empresa_id, self._pg_url).listar(**kwargs)
    def crear_siguiente(self, empresa_id, *, fecha, cuenta_pgc, importe_centimos, concepto, creado_por, **kwargs):
        repo = RepositorioAsiento(empresa_id, self._pg_url)
        ultimo_idx = repo.ultimo_indice()
        ultimo = repo.obtener(ultimo_idx) if ultimo_idx >= 0 else None
        hash_previo = ultimo['hash'] if ultimo else GENESIS
        acto = crear_asiento(
            indice=ultimo_idx + 1, fecha=fecha, concepto=concepto,
            lineas=[
                Linea(cuenta_pgc, debe_centimos=importe_centimos),
                Linea('555', haber_centimos=importe_centimos),
            ],
            hash_previo=hash_previo,
        )
        guardar_asiento(acto, pg_url=self._pg_url, empresa_id=empresa_id)
        return acto
    def verificar_cadena(self, empresa_id, **kwargs):
        return RepositorioAsiento(empresa_id, self._pg_url).verificar_cadena(**kwargs)
    def borrar(self, empresa_id, indice, motivo="Anulación vía backend", actor="backend"):
        return revertir_asiento(
            indice_original=indice, motivo=motivo, actor=actor,
            pg_url=self._pg_url, empresa_id=empresa_id,
        )


class BackendHTTP(BackendContable):
    def __init__(self, base_url, timeout=30.0):
        self._base_url = base_url.rstrip('/')
        self._timeout = timeout
    def _client(self):
        import httpx
        return httpx.Client(timeout=self._timeout)
    def obtener(self, empresa_id, indice):
        with self._client() as c:
            r = c.get(f'{self._base_url}/asientos/{indice}', params={'empresa_id': empresa_id})
            if r.status_code == 404: return None
            r.raise_for_status()
            return r.json()
    def listar(self, empresa_id, **kwargs):
        # Convertir objetos date a isoformat si vienen en los kwargs para la query HTTP
        params = {'empresa_id': empresa_id}
        for k, v in kwargs.items():
            if isinstance(v, date):
                params[k] = v.isoformat()
            else:
                params[k] = v
        with self._client() as c:
            r = c.get(f'{self._base_url}/asientos', params=params)
            r.raise_for_status()
            return r.json()
    def crear_siguiente(self, empresa_id, *, fecha, cuenta_pgc, importe_centimos, concepto, creado_por, **kwargs):
        payload = {'empresa_id': empresa_id, 'fecha': fecha.isoformat(), 'cuenta_pgc': cuenta_pgc, 'importe_centimos': importe_centimos, 'concepto': concepto, 'creado_por': creado_por, **kwargs}
        with self._client() as c:
            r = c.post(f'{self._base_url}/asientos', json=payload)
            r.raise_for_status()
            data = r.json()
            lineas = tuple(Linea(cuenta_pgc=l['cuenta_pgc'], debe_centimos=l['debe_centimos'], haber_centimos=l['haber_centimos'], parrafo_pgc_id=l.get('parrafo_pgc_id'), concepto_linea=l.get('concepto_linea')) for l in data['lineas'])
            return Asiento(indice=data['indice'], fecha=date.fromisoformat(data['fecha']), concepto=data['concepto'], lineas=lineas, hash_previo=data['hash_previo'], hash=data['hash'], huella_contenido=data['huella_contenido'], metadatos=data.get('metadatos', {}))
    def verificar_cadena(self, empresa_id, **kwargs):
        with self._client() as c:
            r = c.post(f'{self._base_url}/verificar', json={'empresa_id': empresa_id, **kwargs})
            r.raise_for_status()
            data = r.json()
            return ReporteCadenaAsientos(empresa_id=empresa_id, desde=data['desde'], hasta=data['hasta'], total=data['total'], cadena_valida=data['cadena_valida'], roturas=data['roturas'])
    def borrar(self, empresa_id, indice, motivo="Anulación vía backend", actor="backend"):
        raise NotImplementedError(
            "El backend HTTP no ofrece borrado ni reversión; solicita un endpoint de reversión explícito."
        )


def get_backend():
    modo = os.environ.get('CONTA_BACKEND', 'postgres').lower()
    if modo == 'postgres':
        return BackendPostgres()
    if modo == 'http':
        url = os.environ.get('CONTA_HTTP_URL')
        if not url:
            raise ValueError('CONTA_BACKEND=http requiere CONTA_HTTP_URL')
        return BackendHTTP(url)
    raise ValueError(f'CONTA_BACKEND desconocido: {modo}')
