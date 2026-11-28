"""Adaptador PostgreSQL para importación reversible del dominio.

Permanece fuera del núcleo estable: conserva el modelo heredado y no acredita
como hechos epistémicos los asientos importados.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime
from typing import Any, Optional

from ..migracion import CorrespondenciaHeredada


class ImportadorCorrespondenciasPostgres:
    """Importa sólo correspondencias reversibles, sin alterar asientos heredados."""

    def __init__(
        self,
        pg_url: Optional[str] = None,
        conexion: Any = None,
        conexion_factory: Any = None,
    ) -> None:
        self.pg_url = pg_url
        self._conexion_externa = conexion
        self._conexion_factory = conexion_factory

    def _conectar(self) -> Any:
        if self._conexion_externa is not None:
            return self._conexion_externa
        if self._conexion_factory is not None:
            return self._conexion_factory(self.pg_url)

        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError("El controlador PostgreSQL 'psycopg' no está disponible") from exc

        if not self.pg_url:
            from ...config.postgresql import PG_URL

            url = PG_URL
        else:
            url = self.pg_url
        return psycopg.connect(url)

    @staticmethod
    def destino_id(empresa_id: str, indice: int) -> str:
        return f"REP-{empresa_id}-{indice}"

    def _validar_asientos(
        self, asientos: Iterable[Mapping[str, Any]], empresa_id: str
    ) -> list[Mapping[str, Any]]:
        if not empresa_id or not empresa_id.strip():
            raise ValueError("empresa_id no puede estar vacío")
        filas = [dict(fila) for fila in asientos]
        claves: set[tuple[str, int]] = set()
        for fila in filas:
            empresa = str(fila.get("empresa_id", "")).strip()
            valor_indice = fila.get("indice")
            if isinstance(valor_indice, bool) or (
                isinstance(valor_indice, float) and not valor_indice.is_integer()
            ):
                raise ValueError("El índice del asiento debe ser entero")
            try:
                indice = int(valor_indice)
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError("Cada asiento importable debe tener empresa_id e indice") from exc

            if not empresa:
                raise ValueError("empresa_id no puede estar vacío")
            if empresa != empresa_id:
                raise ValueError(f"El asiento {empresa}:{indice} no pertenece a {empresa_id}")
            if indice <= 0:
                raise ValueError("El índice del asiento debe ser positivo")
            clave = (empresa, indice)
            if clave in claves:
                raise ValueError(f"Asiento duplicado: {empresa}:{indice}")
            claves.add(clave)

        return filas

    def ensayar_importacion(
        self,
        empresa_id: str,
        asientos: Iterable[Mapping[str, Any]],
    ) -> tuple[list[CorrespondenciaHeredada], dict[str, Any]]:
        """Inserta temporalmente las correspondencias y siempre ejecuta rollback."""
        filas = self._validar_asientos(asientos, empresa_id)
        correspondencias = [
            CorrespondenciaHeredada(
                origen_tipo="ASIENTO_CONTABLE_HEREDADO",
                origen_empresa=empresa_id,
                origen_indice=int(fila["indice"]),
                destino_tipo="REPRESENTACION_CONTABLE",
                destino_id=self.destino_id(empresa_id, int(fila["indice"])),
                estado_migracion="IMPORTADO_SIN_ACREDITACION_EPSTEMICA",
                observaciones=("Ensayo reversible PostgreSQL",),
            )
            for fila in filas
            if str(fila.get("empresa_id", empresa_id)) == empresa_id
        ]

        try:
            from psycopg.types.json import Jsonb
        except ImportError:
            Jsonb = lambda value: value

        conexion = self._conectar()
        try:
            with conexion.cursor() as cursor:
                for correspondencia in correspondencias:
                    cursor.execute(
                        """
                        INSERT INTO dominio_correspondencia_heredada
                            (entidad_id, origen_tipo, origen_indice, destino_tipo,
                             destino_id, estado_migracion, observaciones)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (entidad_id, origen_tipo, origen_indice,
                                     destino_tipo, destino_id) DO UPDATE
                        SET estado_migracion = EXCLUDED.estado_migracion,
                            observaciones = EXCLUDED.observaciones
                        """,
                        (
                            empresa_id,
                            correspondencia.origen_tipo,
                            correspondencia.origen_indice,
                            correspondencia.destino_tipo,
                            correspondencia.destino_id,
                            correspondencia.estado_migracion,
                            Jsonb(list(correspondencia.observaciones)),
                        ),
                    )

                cursor.execute(
                    """
                    SELECT COUNT(*) AS legado,
                           COALESCE(SUM(debe), 0) AS debe,
                           COALESCE(SUM(haber), 0) AS haber
                    FROM (
                        SELECT 0::numeric AS debe, 0::numeric AS haber
                        WHERE FALSE
                    ) AS vacio
                    """
                )

            conexion.rollback()
            reporte = {
                "empresa_id": empresa_id,
                "total_correspondencias": len(correspondencias),
                "persistido": False,
                "rollback": True,
            }
            return correspondencias, reporte
        except Exception:
            conexion.rollback()
            raise
        finally:
            if self._conexion_externa is None:
                conexion.close()

    def confirmar_importacion(
        self,
        empresa_id: str,
        asientos: Iterable[Mapping[str, Any]],
    ) -> list[CorrespondenciaHeredada]:
        """Persiste correspondencias; no modifica el ledger heredado."""
        filas = self._validar_asientos(asientos, empresa_id)
        correspondencias = [
            CorrespondenciaHeredada(
                origen_tipo="ASIENTO_CONTABLE_HEREDADO",
                origen_empresa=empresa_id,
                origen_indice=int(fila["indice"]),
                destino_tipo="REPRESENTACION_CONTABLE",
                destino_id=self.destino_id(empresa_id, int(fila["indice"])),
                estado_migracion="IMPORTADO_SIN_ACREDITACION_EPSTEMICA",
                observaciones=tuple(
                    str(valor) for valor in fila.get("observaciones", ())
                ) if fila.get("observaciones") is not None else (),
            )
            for fila in filas
            if str(fila.get("empresa_id", empresa_id)) == empresa_id
        ]

        try:
            from psycopg.types.json import Jsonb
        except ImportError:
            Jsonb = lambda value: value

        conexion = self._conectar()
        try:
            with conexion.cursor() as cursor:
                for correspondencia in correspondencias:
                    cursor.execute(
                        """
                        INSERT INTO dominio_correspondencia_heredada
                            (entidad_id, origen_tipo, origen_indice, destino_tipo,
                             destino_id, estado_migracion, observaciones)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (entidad_id, origen_tipo, origen_indice,
                                     destino_tipo, destino_id) DO NOTHING
                        """,
                        (
                            empresa_id,
                            correspondencia.origen_tipo,
                            correspondencia.origen_indice,
                            correspondencia.destino_tipo,
                            correspondencia.destino_id,
                            correspondencia.estado_migracion,
                            Jsonb(list(correspondencia.observaciones)),
                        ),
                    )
            conexion.commit()
            return correspondencias
        except Exception:
            conexion.rollback()
            raise
        finally:
            if self._conexion_externa is None:
                conexion.close()


class RepositorioPermisosEvento:
    """Permisos leídos y escritos exclusivamente desde `dominio_evento`."""

    def __init__(
        self,
        pg_url: Optional[str] = None,
        conexion: Any = None,
        conexion_factory: Any = None,
    ) -> None:
        self.pg_url = pg_url
        self._conexion_externa = conexion
        self._conexion_factory = conexion_factory

    def _conectar(self) -> Any:
        if self._conexion_externa is not None:
            return self._conexion_externa
        if self._conexion_factory is not None:
            return self._conexion_factory(self.pg_url)
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError("El controlador PostgreSQL 'psycopg' no está disponible") from exc
        if not self.pg_url:
            from ...config.postgresql import PG_URL

            url = PG_URL
        else:
            url = self.pg_url
        return psycopg.connect(url)

    @staticmethod
    def _fecha(valor: Any) -> Optional[datetime]:
        if isinstance(valor, datetime):
            return valor
        if valor is None:
            return None
        return datetime.fromisoformat(str(valor))

    @staticmethod
    def _rol(valor: Any) -> Any:
        from ..entidades.contables import Rol

        texto = valor.value if hasattr(valor, "value") else str(valor)
        if texto in Rol.__members__:
            return Rol[texto]
        return Rol(texto)

    @staticmethod
    def _evento_desde_fila(fila: Mapping[str, Any]) -> Any:
        from ..entidades.contables import Evento

        evento = Evento(
            evento_id=str(fila["evento_id"]),
            tipo=str(fila["tipo"]),
            objeto_id=str(fila["objeto_id"]),
            actor_id=str(fila["actor_id"]),
            timestamp=fila["timestamp"],
            estado_anterior=fila.get("estado_anterior"),
            estado_posterior=fila.get("estado_posterior"),
            motivo=str(fila.get("motivo") or ""),
            referencia_ids=tuple(fila.get("referencias") or ()),
            payload=dict(fila.get("payload") or {}),
        )
        evento.indice = fila["indice"]
        evento.huella = fila["huella"]
        evento.hash_previo = fila["hash_previo"]
        evento.hash = fila["hash"]
        return evento

    def listar_eventos(self, entidad_id: str) -> list[dict[str, Any]]:
        from psycopg.rows import dict_row

        conexion = self._conectar()
        try:
            with conexion.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT entidad_id, evento_id, indice, tipo, objeto_tipo,
                           objeto_id, actor_id, timestamp, estado_anterior,
                           estado_posterior, motivo, referencias, payload,
                           huella, hash_previo, hash
                    FROM dominio_evento
                    WHERE entidad_id = %s
                    ORDER BY indice
                    """,
                    (entidad_id,),
                )
                return [dict(fila) for fila in cursor.fetchall()]
        finally:
            if self._conexion_externa is None:
                conexion.close()

    def nucleo_para_entidad(self, entidad_id: str, momento: datetime) -> Any:
        from ..entidades.contables import Actor, PermisoConcedido, Rol
        from ..servicios.nucleo import NucleoEpistemicoContable

        nucleo = NucleoEpistemicoContable()
        nucleo.eventos = [
            self._evento_desde_fila(fila) for fila in self.listar_eventos(entidad_id)
        ]
        estado = nucleo.reconstruir(momento)
        for actor_id, datos in estado["actores"].items():
            nucleo.actores[str(actor_id)] = Actor(
                actor_id=str(actor_id),
                nombre=str(datos.get("nombre") or actor_id),
                tipo=str(datos.get("tipo") or "HUMANO"),
                rol=self._rol(datos.get("rol") or Rol.OPERARIO),
            )
        for permiso_id, datos in estado["permisos"].items():
            nucleo.permisos[str(permiso_id)] = PermisoConcedido(
                permiso_id=str(permiso_id),
                otorgante_id=str(datos["otorgante_id"]),
                beneficiario_id=str(datos["beneficiario_id"]),
                competencia=str(datos["competencia"]),
                alcance=str(datos["alcance"]),
                otorgada_en=self._fecha(datos["otorgada_en"]),
                vigente_hasta=self._fecha(datos.get("vigente_hasta")),
                revocada_en=self._fecha(datos.get("revocada_en")),
            )
        return nucleo

    def tiene_permiso(
        self,
        entidad_id: str,
        beneficiario_id: str,
        competencia: str,
        alcance: str,
        momento: datetime,
    ) -> bool:
        nucleo = self.nucleo_para_entidad(entidad_id, momento)
        for permiso in nucleo.permisos.values():
            if (
                permiso.beneficiario_id == beneficiario_id
                and permiso.competencia == competencia
                and permiso.alcance in (alcance, "*")
                and permiso.revocada_en is None
                and permiso.otorgada_en <= momento
                and (permiso.vigente_hasta is None or momento <= permiso.vigente_hasta)
            ):
                return True
        return False

    def _persistir_eventos(self, entidad_id: str, eventos: Iterable[Any]) -> None:
        from psycopg.types.json import Jsonb

        from ..servicios.nucleo import _normalizar_json

        conexion = self._conectar()
        try:
            with conexion.cursor() as cursor:
                for evento in eventos:
                    objeto_tipo = str(evento.tipo).split("_", 1)[0].lower()
                    cursor.execute(
                        """
                        INSERT INTO dominio_evento (
                            entidad_id, evento_id, indice, tipo, objeto_tipo,
                            objeto_id, actor_id, timestamp, estado_anterior,
                            estado_posterior, motivo, referencias, payload,
                            huella, hash_previo, hash
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (entidad_id, evento_id) DO NOTHING
                        """,
                        (
                            entidad_id,
                            evento.evento_id,
                            evento.indice,
                            evento.tipo,
                            objeto_tipo,
                            evento.objeto_id,
                            evento.actor_id,
                            evento.timestamp,
                            Jsonb(_normalizar_json(evento.estado_anterior)),
                            Jsonb(_normalizar_json(evento.estado_posterior)),
                            evento.motivo,
                            Jsonb(list(evento.referencia_ids)),
                            Jsonb(_normalizar_json(evento.payload)),
                            evento.huella,
                            evento.hash_previo,
                            evento.hash,
                        ),
                    )
            conexion.commit()
        except Exception:
            conexion.rollback()
            raise
        finally:
            if self._conexion_externa is None:
                conexion.close()

    def conceder(
        self,
        entidad_id: str,
        permiso_id: str,
        otorgante_id: str,
        otorgante_rol: Any,
        beneficiario_id: str,
        beneficiario_rol: Any,
        competencia: str,
        alcance: str,
        otorgada_en: datetime,
        vigente_hasta: Optional[datetime] = None,
    ) -> None:
        from ..entidades.contables import Actor

        nucleo = self.nucleo_para_entidad(entidad_id, otorgada_en)
        inicial = len(nucleo.eventos)
        if otorgante_id not in nucleo.actores:
            nucleo.registrar_actor(
                Actor(otorgante_id, otorgante_id, rol=self._rol(otorgante_rol)), otorgada_en,
            )
        if beneficiario_id not in nucleo.actores:
            nucleo.registrar_actor(
                Actor(beneficiario_id, beneficiario_id, rol=self._rol(beneficiario_rol)), otorgada_en,
            )
        nucleo.conceder_permiso(
            permiso_id, otorgante_id, beneficiario_id, competencia, alcance,
            otorgada_en, vigente_hasta,
        )
        self._persistir_eventos(entidad_id, nucleo.eventos[inicial:])

    def revocar(
        self,
        entidad_id: str,
        permiso_id: str,
        actor_id: str,
        motivo: str,
        revocada_en: datetime,
    ) -> None:
        nucleo = self.nucleo_para_entidad(entidad_id, revocada_en)
        inicial = len(nucleo.eventos)
        nucleo.revocar_permiso(permiso_id, actor_id, motivo, revocada_en)
        self._persistir_eventos(entidad_id, nucleo.eventos[inicial:])
