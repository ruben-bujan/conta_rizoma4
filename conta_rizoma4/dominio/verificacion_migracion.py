"""Verificación reversible de migración heredada en memoria.

No accede a PostgreSQL ni modifica datos externos. Compara una copia importada
con el conjunto heredado y permite rollback lógico de la operación de prueba.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Optional


@dataclass(frozen=True)
class DiferenciaMigracion:
    objeto_tipo: str
    empresa_id: str
    clave: str
    campo: str
    heredado: Any
    importado: Any


@dataclass
class ResultadoVerificacionMigracion:
    total_heredado: int
    total_importado: int
    correspondencias: int
    diferencias: list[DiferenciaMigracion] = field(default_factory=list)

    @property
    def reversible(self) -> bool:
        return len(self.diferencias) == 0


class PruebaMigracionMemoria:
    """Importación temporal y rollback lógico de una copia del legado."""

    def __init__(self, heredado: Iterable[Mapping[str, Any]]) -> None:
        self._snapshot = deepcopy(list(heredado))
        self._copia_importada: list[Mapping[str, Any]] = []
        self._correspondencias: dict[str, str] = {}

    def importar_copia(self) -> None:
        """Importa una copia profunda sin modificar el conjunto original."""
        self._copia_importada = deepcopy(self._snapshot)

    def agregar_correspondencia(self, origen: str, destino: str) -> None:
        self._correspondencias[origen] = destino

    def rollback_logico(self) -> None:
        """Descarta toda la copia importada y sus correspondencias."""
        self._copia_importada = []
        self._correspondencias = {}

    def verificar(
        self,
        campos: Iterable[str] = ("indice", "empresa_id", "fecha", "concepto", "hash"),
    ) -> ResultadoVerificacionMigracion:
        heredado_por_clave = {
            f"{fila.get('empresa_id')}:{fila.get('indice')}": dict(fila)
            for fila in self._snapshot
        }
        importado_por_clave = {
            f"{fila.get('empresa_id')}:{fila.get('indice')}": dict(fila)
            for fila in self._copia_importada
        }

        diferencias: list[DiferenciaMigracion] = []

        claves = sorted(set(heredado_por_clave) | set(importado_por_clave))
        for clave in claves:
            heredado = heredado_por_clave.get(clave)
            importado = importado_por_clave.get(clave)

            if heredado is None or importado is None:
                diferencias.append(DiferenciaMigracion(
                    objeto_tipo="ASIENTO_CONTABLE",
                    empresa_id=clave.split(":", 1)[0],
                    clave=clave,
                    campo="presencia",
                    heredado=heredado,
                    importado=importado,
                ))
                continue

            for campo in campos:
                if heredado.get(campo) != importado.get(campo):
                    diferencias.append(DiferenciaMigracion(
                        objeto_tipo="ASIENTO_CONTABLE",
                        empresa_id=str(heredado.get("empresa_id")),
                        clave=clave,
                        campo=campo,
                        heredado=heredado.get(campo),
                        importado=importado.get(campo),
                    ))

        return ResultadoVerificacionMigracion(
            total_heredado=len(self._snapshot),
            total_importado=len(self._copia_importada),
            correspondencias=len(self._correspondencias),
            diferencias=diferencias,
        )


@dataclass
class ResultadoVerificacionDual:
    total_heredado: int
    total_postgres: int
    correspondencias: int
    diferencias: list[DiferenciaMigracion] = field(default_factory=list)

    @property
    def reversible(self) -> bool:
        return len(self.diferencias) == 0

    @property
    def activacion_permitida(self) -> bool:
        return (
            self.reversible
            and self.total_heredado == self.total_postgres
            and self.correspondencias == self.total_heredado
        )


def verificar_dual(
    heredado: Iterable[Mapping[str, Any]],
    postgres: Iterable[Mapping[str, Any]],
    correspondencias: Iterable[Any] = (),
) -> ResultadoVerificacionDual:
    """Compara registros heredados y PostgreSQL sin modificar datos."""
    filas_heredadas = [dict(fila) for fila in heredado]
    filas_postgres = [dict(fila) for fila in postgres]
    diferencias: list[DiferenciaMigracion] = []

    def indexar(filas: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        indice: dict[str, dict[str, Any]] = {}
        for fila in filas:
            empresa, numero = fila.get("empresa_id"), fila.get("indice")
            clave = f"{empresa}:{numero}"
            if empresa in (None, "") or numero is None:
                diferencias.append(DiferenciaMigracion(
                    "ASIENTO_CONTABLE", str(empresa or ""), clave, "clave_incompleta",
                    "empresa_id e indice requeridos", fila,
                ))
                continue
            if clave in indice:
                diferencias.append(DiferenciaMigracion(
                    "ASIENTO_CONTABLE", str(empresa), clave, "clave_duplicada",
                    indice[clave], fila,
                ))
                continue
            indice[clave] = fila
        return indice

    clave_heredada = indexar(filas_heredadas)
    clave_postgres = indexar(filas_postgres)
    campos_base = (
        "indice", "empresa_id", "fecha", "concepto", "hash", "estado",
        "total_debe", "total_haber",
    )
    campos_adicionales = (
        "lineas", "documentos", "rectificaciones", "actor_id", "operador",
        "autorizacion_id", "autorizaciones", "evidencias", "fuentes",
        "decision_id", "interpretacion_id", "ejercicio_id",
    )

    for clave in sorted(set(clave_heredada) | set(clave_postgres)):
        fila_heredada = clave_heredada.get(clave)
        fila_postgres = clave_postgres.get(clave)

        if fila_heredada is None or fila_postgres is None:
            diferencias.append(DiferenciaMigracion(
                objeto_tipo="ASIENTO_CONTABLE",
                empresa_id=clave.split(":", 1)[0],
                clave=clave,
                campo="presencia",
                heredado=fila_heredada,
                importado=fila_postgres,
            ))
            continue

        campos = campos_base + tuple(
            campo for campo in campos_adicionales
            if campo in fila_heredada or campo in fila_postgres
        )
        for campo in campos:
            if campo in fila_heredada or campo in fila_postgres:
                if fila_heredada.get(campo) != fila_postgres.get(campo):
                    diferencias.append(DiferenciaMigracion(
                        objeto_tipo="ASIENTO_CONTABLE",
                        empresa_id=str(fila_heredada.get("empresa_id")),
                        clave=clave,
                        campo=campo,
                        heredado=fila_heredada.get(campo),
                        importado=fila_postgres.get(campo),
                    ))

    correspondencias = list(correspondencias)
    claves_correspondencia: set[str] = set()
    destinos: set[str] = set()
    for correspondencia in correspondencias:
        def valor(campo: str, default: Any = None) -> Any:
            if isinstance(correspondencia, Mapping):
                return correspondencia.get(campo, default)
            return getattr(correspondencia, campo, default)

        empresa, numero = valor("origen_empresa"), valor("origen_indice")
        clave = f"{empresa}:{numero}"
        destino_id = valor("destino_id")
        if empresa in (None, "") or numero is None or not destino_id:
            diferencias.append(DiferenciaMigracion(
                "ASIENTO_CONTABLE", str(empresa or ""), clave, "correspondencia_incompleta",
                "origen y destino requeridos", correspondencia,
            ))
            continue
        if valor("origen_tipo") != "ASIENTO_CONTABLE_HEREDADO":
            diferencias.append(DiferenciaMigracion(
                "ASIENTO_CONTABLE", str(empresa), clave, "correspondencia_origen_tipo",
                "ASIENTO_CONTABLE_HEREDADO", valor("origen_tipo"),
            ))
        if valor("destino_tipo") != "REPRESENTACION_CONTABLE":
            diferencias.append(DiferenciaMigracion(
                "ASIENTO_CONTABLE", str(empresa), clave, "correspondencia_destino_tipo",
                "REPRESENTACION_CONTABLE", valor("destino_tipo"),
            ))
        if valor("estado_migracion") != "IMPORTADO_SIN_ACREDITACION_EPSTEMICA":
            diferencias.append(DiferenciaMigracion(
                "ASIENTO_CONTABLE", str(empresa), clave, "estado_migracion",
                "IMPORTADO_SIN_ACREDITACION_EPSTEMICA", valor("estado_migracion"),
            ))
        if clave in claves_correspondencia:
            diferencias.append(DiferenciaMigracion(
                "ASIENTO_CONTABLE", str(empresa), clave, "correspondencia_duplicada",
                "una correspondencia por asiento", destino_id,
            ))
        claves_correspondencia.add(clave)
        if destino_id in destinos:
            diferencias.append(DiferenciaMigracion(
                "ASIENTO_CONTABLE", str(empresa), clave, "destino_duplicado",
                "destino único", destino_id,
            ))
        destinos.add(destino_id)
        if clave not in clave_heredada:
            diferencias.append(DiferenciaMigracion(
                "ASIENTO_CONTABLE", str(empresa), clave, "correspondencia_sobrante",
                None, destino_id,
            ))

    for clave in clave_heredada:
        if clave not in claves_correspondencia:
            diferencias.append(DiferenciaMigracion(
                objeto_tipo="ASIENTO_CONTABLE",
                empresa_id=clave.split(":", 1)[0],
                clave=clave,
                campo="correspondencia",
                heredado=True,
                importado=False,
            ))

    return ResultadoVerificacionDual(
        total_heredado=len(filas_heredadas),
        total_postgres=len(filas_postgres),
        correspondencias=len(claves_correspondencia),
        diferencias=diferencias,
    )


def verificar_conjunto(
    heredado: Iterable[Mapping[str, Any]],
    campos: Iterable[str] = ("indice", "empresa_id", "fecha", "concepto", "hash"),
) -> tuple[PruebaMigracionMemoria, ResultadoVerificacionMigracion]:
    prueba = PruebaMigracionMemoria(heredado)
    prueba.importar_copia()
    for fila in prueba._copia_importada:
        clave = f"{fila.get('empresa_id')}:{fila.get('indice')}"
        prueba.agregar_correspondencia(clave, f"REP-{clave}")
    resultado = prueba.verificar(campos)
    return prueba, resultado
