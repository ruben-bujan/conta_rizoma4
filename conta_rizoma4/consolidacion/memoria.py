"""Consolidación empresarial pura en memoria con reconstrucción epistemológica.

Los saldos usan la convención del mayor: debe positivo y haber negativo.
Este módulo no decide criterios normativos ni convierte propuestas en hechos.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional

from .modelo import ConsolidacionError


@dataclass(frozen=True)
class RelacionParticipacion:
    matriz_id: str
    filial_id: str
    porcentaje: float
    vigente_desde: date
    vigente_hasta: Optional[date] = None
    conocida_desde: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.matriz_id or not self.filial_id or self.matriz_id == self.filial_id:
            raise ConsolidacionError("La relación requiere entidades distintas")
        if not 0 < self.porcentaje <= 100:
            raise ConsolidacionError("La participación debe estar en (0, 100]")
        if self.vigente_hasta and self.vigente_hasta < self.vigente_desde:
            raise ConsolidacionError("La vigencia termina antes de comenzar")


@dataclass(frozen=True)
class BalanceIndividual:
    empresa_id: str
    fecha_cierre: date
    saldos: dict[str, int]
    resultado: int = 0
    conocido_desde: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    evidencia_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.empresa_id:
            raise ConsolidacionError("empresa_id es obligatorio")
        if any(not cuenta for cuenta in self.saldos):
            raise ConsolidacionError("Todas las cuentas deben tener código")


@dataclass(frozen=True)
class EliminacionConsolidacion:
    eliminacion_id: str
    grupo_id: str
    fecha_cierre: date
    ajustes_por_empresa: dict[str, dict[str, int]]
    motivo: str
    evidencia_ids: tuple[str, ...]
    propuesta_por: str
    propuesta_en: datetime
    autorizada_por: Optional[str] = None
    autorizacion_id: Optional[str] = None
    autorizada_en: Optional[datetime] = None


@dataclass(frozen=True)
class EventoConsolidacion:
    tipo: str
    objeto: object
    registrado_en: datetime


@dataclass(frozen=True)
class FinalizacionRelacion:
    matriz_id: str
    filial_id: str
    relacion_vigente_desde: date
    efectiva_desde: date


@dataclass
class ResultadoConsolidacion:
    grupo_id: str
    fecha_cierre: date
    reconstruido_a: datetime
    empresas: tuple[str, ...]
    participaciones_indirectas: dict[str, float]
    saldos_individuales: dict[str, dict[str, int]]
    saldos_suma: dict[str, int]
    eliminaciones_propuestas: tuple[EliminacionConsolidacion, ...]
    eliminaciones_aplicadas: tuple[EliminacionConsolidacion, ...]
    saldos_consolidados: dict[str, int]
    resultado_grupo: int
    resultado_matriz: int
    resultado_minoritarios: int
    descuadre_centimos: int
    cuadra: bool


class RepositorioConsolidacionMemoria:
    """Registro append-only en memoria; toda consulta histórica usa conocido_en."""

    def __init__(self) -> None:
        self._eventos: list[EventoConsolidacion] = []

    @property
    def eventos(self) -> tuple[EventoConsolidacion, ...]:
        """Vista aislada del registro; mutar el resultado no altera el historial."""
        return tuple(deepcopy(self._eventos))

    def _registrar(self, tipo: str, objeto: object, registrado_en: datetime) -> None:
        if registrado_en.tzinfo is None or registrado_en.utcoffset() is None:
            raise ConsolidacionError("Las fechas de conocimiento deben incluir zona horaria")
        if self._eventos and registrado_en < self._eventos[-1].registrado_en:
            raise ConsolidacionError("Los eventos deben registrarse en orden temporal")
        self._eventos.append(EventoConsolidacion(tipo, deepcopy(objeto), registrado_en))

    def registrar_relacion(self, relacion: RelacionParticipacion) -> None:
        self._registrar("RELACION", relacion, relacion.conocida_desde)

    def finalizar_relacion(
        self, matriz_id: str, filial_id: str, efectiva_desde: date, conocida_en: datetime
    ) -> None:
        """Registra el fin de vigencia sin reescribir la relación histórica."""
        previos = self.reconstruir_eventos(conocida_en)
        relaciones = [
            e.objeto for e in previos
            if e.tipo == "RELACION" and isinstance(e.objeto, RelacionParticipacion)
            and e.objeto.matriz_id == matriz_id and e.objeto.filial_id == filial_id
            and e.objeto.vigente_desde <= efectiva_desde
            and (e.objeto.vigente_hasta is None or efectiva_desde <= e.objeto.vigente_hasta)
        ]
        finales = [
            e.objeto for e in previos
            if e.tipo == "RELACION_FINALIZADA" and isinstance(e.objeto, FinalizacionRelacion)
            and e.objeto.matriz_id == matriz_id and e.objeto.filial_id == filial_id
        ]
        if not relaciones:
            raise ConsolidacionError("No hay una relación activa que pueda finalizar en esa fecha")
        relacion = max(relaciones, key=lambda r: r.vigente_desde)
        if any(f.relacion_vigente_desde == relacion.vigente_desde for f in finales):
            raise ConsolidacionError("No hay una relación activa que pueda finalizar en esa fecha")
        self._registrar(
            "RELACION_FINALIZADA",
            FinalizacionRelacion(matriz_id, filial_id, relacion.vigente_desde, efectiva_desde),
            conocida_en,
        )

    def registrar_balance(self, balance: BalanceIndividual) -> None:
        self._registrar("BALANCE", balance, balance.conocido_desde)

    def proponer_eliminacion(self, eliminacion: EliminacionConsolidacion) -> None:
        if not eliminacion.eliminacion_id or not eliminacion.grupo_id or not eliminacion.motivo or not eliminacion.propuesta_por:
            raise ConsolidacionError("La propuesta requiere id, grupo, motivo y actor")
        if eliminacion.autorizacion_id or eliminacion.autorizada_por:
            raise ConsolidacionError("Una propuesta no puede venir preautorizada")
        if not eliminacion.ajustes_por_empresa or any(
            not empresa or any(not cuenta for cuenta in saldos)
            for empresa, saldos in eliminacion.ajustes_por_empresa.items()
        ):
            raise ConsolidacionError("La propuesta requiere ajustes con empresa y cuenta identificables")
        if any(
            e.tipo == "ELIMINACION_PROPUESTA" and getattr(e.objeto, "eliminacion_id", None) == eliminacion.eliminacion_id
            for e in self._eventos
        ):
            raise ConsolidacionError("Identificador de eliminación duplicado")
        self._registrar("ELIMINACION_PROPUESTA", eliminacion, eliminacion.propuesta_en)

    def autorizar_eliminacion(
        self, eliminacion_id: str, actor_id: str, autorizacion_id: str, cuando: datetime
    ) -> EliminacionConsolidacion:
        if not actor_id or not autorizacion_id:
            raise ConsolidacionError("La autorización requiere actor e identificador")
        anterior = self.reconstruir_eventos(cuando)
        propuesta = next(
            (e.objeto for e in reversed(anterior)
             if e.tipo == "ELIMINACION_PROPUESTA"
             and isinstance(e.objeto, EliminacionConsolidacion)
             and e.objeto.eliminacion_id == eliminacion_id),
            None,
        )
        if propuesta is None:
            raise ConsolidacionError("No existe una propuesta conocida en esa fecha")
        if any(e.tipo == "ELIMINACION_AUTORIZADA" and getattr(e.objeto, "eliminacion_id", None) == eliminacion_id for e in anterior):
            raise ConsolidacionError("La eliminación ya fue autorizada")
        autorizada = EliminacionConsolidacion(
            **{**propuesta.__dict__, "autorizada_por": actor_id,
               "autorizacion_id": autorizacion_id, "autorizada_en": cuando}
        )
        self._registrar("ELIMINACION_AUTORIZADA", autorizada, cuando)
        return autorizada

    def reconstruir_eventos(self, conocido_a: datetime) -> list[EventoConsolidacion]:
        if conocido_a.tzinfo is None or conocido_a.utcoffset() is None:
            raise ConsolidacionError("La fecha de reconstrucción debe incluir zona horaria")
        return [deepcopy(e) for e in self._eventos if e.registrado_en <= conocido_a]

    def consolidar(
        self, grupo_id: str, matriz_id: str, fecha_cierre: date, conocido_a: datetime
    ) -> ResultadoConsolidacion:
        eventos = self.reconstruir_eventos(conocido_a)
        relaciones = [e.objeto for e in eventos if e.tipo == "RELACION" and isinstance(e.objeto, RelacionParticipacion)]
        finales = [e.objeto for e in eventos if e.tipo == "RELACION_FINALIZADA" and isinstance(e.objeto, FinalizacionRelacion)]
        activos = [
            r for r in relaciones
            if r.vigente_desde <= fecha_cierre
            and (r.vigente_hasta is None or fecha_cierre <= r.vigente_hasta)
            and not any(f.matriz_id == r.matriz_id and f.filial_id == r.filial_id
                        and f.relacion_vigente_desde == r.vigente_desde
                        and fecha_cierre >= f.efectiva_desde for f in finales)
        ]
        pares_activos = [(r.matriz_id, r.filial_id) for r in activos]
        if len(pares_activos) != len(set(pares_activos)):
            raise ConsolidacionError("Hay relaciones de participación activas duplicadas")
        participaciones = {matriz_id: 100.0}
        matriz_de: dict[str, str] = {}
        pendientes = [matriz_id]
        while pendientes:
            padre = pendientes.pop(0)
            pct_padre = participaciones[padre]
            for relacion in activos:
                if relacion.matriz_id != padre:
                    continue
                pct = pct_padre * relacion.porcentaje / 100
                if relacion.filial_id in matriz_de and matriz_de[relacion.filial_id] != padre:
                    raise ConsolidacionError("Una filial tiene varias matrices activas")
                previo = participaciones.get(relacion.filial_id)
                if previo is not None:
                    raise ConsolidacionError("Estructura circular o múltiples participaciones: requiere criterio explícito")
                if previo is None:
                    matriz_de[relacion.filial_id] = padre
                    participaciones[relacion.filial_id] = pct
                    pendientes.append(relacion.filial_id)

        balances: dict[str, BalanceIndividual] = {}
        for ev in eventos:
            if ev.tipo == "BALANCE" and isinstance(ev.objeto, BalanceIndividual):
                b = ev.objeto
                if b.fecha_cierre == fecha_cierre and b.empresa_id in participaciones:
                    balances[b.empresa_id] = b
        faltantes = set(participaciones) - set(balances)
        if faltantes:
            raise ConsolidacionError(f"Falta balance individual para: {', '.join(sorted(faltantes))}")

        propuestas: dict[str, EliminacionConsolidacion] = {}
        autorizadas: dict[str, EliminacionConsolidacion] = {}
        for ev in eventos:
            if isinstance(ev.objeto, EliminacionConsolidacion) and ev.objeto.fecha_cierre == fecha_cierre and ev.objeto.grupo_id == grupo_id:
                if ev.tipo == "ELIMINACION_PROPUESTA":
                    propuestas[ev.objeto.eliminacion_id] = ev.objeto
                elif ev.tipo == "ELIMINACION_AUTORIZADA":
                    autorizadas[ev.objeto.eliminacion_id] = ev.objeto

        suma: dict[str, int] = {}
        resultado_por_empresa = {empresa: balance.resultado for empresa, balance in balances.items()}
        for empresa, balance in balances.items():
            for cuenta, importe in balance.saldos.items():
                suma[cuenta] = suma.get(cuenta, 0) + importe
        consolidados = dict(suma)
        for eliminacion in autorizadas.values():
            for empresa, saldos in eliminacion.ajustes_por_empresa.items():
                if empresa not in participaciones:
                    raise ConsolidacionError(f"Eliminación {eliminacion.eliminacion_id}: {empresa} no pertenece al grupo")
                for cuenta, importe in saldos.items():
                    consolidados[cuenta] = consolidados.get(cuenta, 0) + importe
                    if cuenta[0] in ("6", "7"):
                        resultado_por_empresa[empresa] = resultado_por_empresa.get(empresa, 0) - importe
        descuadre = sum(consolidados.values())
        resultado_grupo = sum(resultado_por_empresa.values())
        resultado_matriz = round(sum(resultado * participaciones[e] / 100 for e, resultado in resultado_por_empresa.items()))
        resultado_minoritarios = resultado_grupo - resultado_matriz
        return ResultadoConsolidacion(
            grupo_id=grupo_id, fecha_cierre=fecha_cierre, reconstruido_a=conocido_a,
            empresas=tuple(sorted(participaciones)), participaciones_indirectas=participaciones,
            saldos_individuales={e: dict(b.saldos) for e, b in balances.items()},
            saldos_suma=suma, eliminaciones_propuestas=tuple(propuestas.values()),
            eliminaciones_aplicadas=tuple(autorizadas.values()), saldos_consolidados=consolidados,
            resultado_grupo=resultado_grupo, resultado_matriz=resultado_matriz,
            resultado_minoritarios=resultado_minoritarios, descuadre_centimos=descuadre,
            cuadra=descuadre == 0,
        )
