"""Núcleo de dominio y ledger en memoria de la POC."""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime
from typing import Any, Iterable, Optional

from .modelo import (
    Actor, Autorizacion, Criterio, Decision, EntidadContable, EstadoDecision,
    EstadoEpistemologico, EstadoInterpretacion, EstadoRepresentacion, Evidencia,
    Fuente, HechoEconomico, Interpretacion, Linea, Rectificacion,
    RepresentacionContable, Evento, ValoracionEvidencia,
)


class ErrorDominio(ValueError):
    pass


class NucleoEpistemicoContable:
    def __init__(self) -> None:
        self.entidades: dict[str, EntidadContable] = {}
        self.actores: dict[str, Actor] = {}
        self.fuentes: dict[str, Fuente] = {}
        self.evidencias: dict[str, Evidencia] = {}
        self.heuristic_evidencias: dict[tuple[str, str], ValoracionEvidencia] = {}
        self.hechos: dict[str, HechoEconomico] = {}
        self.criterios: dict[str, Criterio] = {}
        self.interpretaciones: dict[str, Interpretacion] = {}
        self.autorizaciones: dict[str, Autorizacion] = {}
        self.decisiones: dict[str, Decision] = {}
        self.representaciones: dict[str, RepresentacionContable] = {}
        self.rectificaciones: dict[str, Rectificacion] = {}
        self.eventos: list[Evento] = []

    def _registrar_evento(
        self,
        tipo: str,
        objeto_id: str,
        actor_id: str,
        timestamp: datetime,
        anterior: Any,
        posterior: Any,
        motivo: str,
        referencia_ids: Iterable[str] = (),
        payload: Optional[dict[str, Any]] = None,
    ) -> Evento:
        previo = self.eventos[-1].hash if self.eventos else "0" * 64
        numero = len(self.eventos) + 1
        canonico = {
            "tipo": tipo,
            "objeto_id": objeto_id,
            "actor_id": actor_id,
            "timestamp": timestamp.isoformat(),
            "motivo": motivo,
            "referencias": list(referencia_ids),
            "payload": payload or {},
        }
        huella = hashlib.sha256(
            json.dumps(canonico, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        valor = hashlib.sha256(f"{previo}|{huella}|{numero}".encode("utf-8")).hexdigest()
        evento = Evento(
            evento_id=f"EV-{numero:06d}",
            tipo=tipo,
            objeto_id=objeto_id,
            actor_id=actor_id,
            timestamp=timestamp,
            estado_anterior=deepcopy(anterior),
            estado_posterior=deepcopy(posterior),
            motivo=motivo,
            referencia_ids=tuple(referencia_ids),
            payload=payload or {},
        )
        evento.hash = valor  # atributo dinámico deliberadamente separado del modelo histórico
        evento.huella = huella
        evento.hash_previo = previo
        evento.indice = numero
        self.eventos.append(evento)
        return evento

    def registrar_entidad(self, entidad: EntidadContable, actor_id: str, ahora: datetime) -> EntidadContable:
        if entidad.entidad_id in self.entidades:
            raise ErrorDominio("Entidad duplicada")
        self.entidades[entidad.entidad_id] = entidad
        self._registrar_evento("ENTIDAD_REGISTRADA", entidad.entidad_id, actor_id, ahora,
                              None, entidad.__dict__, "Alta de entidad")
        return entidad

    def registrar_actor(self, actor: Actor, ahora: datetime) -> Actor:
        if actor.actor_id in self.actores:
            raise ErrorDominio("Actor duplicado")
        self.actores[actor.actor_id] = actor
        self._registrar_evento("ACTOR_REGISTRADO", actor.actor_id, actor.actor_id, ahora,
                              None, actor.__dict__, "Alta de actor")
        return actor

    def registrar_hecho(self, hecho: HechoEconomico, actor_id: str) -> HechoEconomico:
        if hecho.hecho_id in self.hechos:
            raise ErrorDominio("Hecho duplicado")
        if hecho.entidad_id not in self.entidades:
            raise ErrorDominio("Entidad inexistente")
        if actor_id not in self.actores:
            raise ErrorDominio("Actor inexistente")
        anterior = None
        posterior = hecho.estado_epistemologico.value
        self.hechos[hecho.hecho_id] = hecho
        self._registrar_evento("HECHO_REGISTRADO", hecho.hecho_id, actor_id,
                              hecho.registrado_en, anterior, posterior,
                              "Registro inicial del hecho", (hecho.entidad_id,),
                              {"tipo": hecho.tipo, "estado_economico": hecho.estado_economico})
        return hecho

    def relacionar_hechos(self, origen: str, destino: str, relacion: str,
                          actor_id: str, ahora: datetime, motivo: str) -> None:
        if origen not in self.hechos or destino not in self.hechos:
            raise ErrorDominio("Hecho inexistente")
        if origen == destino:
            raise ErrorDominio("Un hecho no puede relacionarse consigo mismo")
        anterior = dict(self.hechos[origen].relaciones)
        self.hechos[origen].relaciones[f"{relacion}:{destino}"] = destino
        posterior = dict(self.hechos[origen].relaciones)
        self._registrar_evento("HECHO_RELACIONADO", origen, actor_id, ahora,
                              anterior, posterior, motivo, (destino,), {"relacion": relacion})

    def cambiar_estado_epistemologico(self, hecho_id: str, nuevo: EstadoEpistemologico,
                                      actor_id: str, ahora: datetime, motivo: str,
                                      evidencia_ids: Iterable[str] = ()) -> HechoEconomico:
        if hecho_id not in self.hechos:
            raise ErrorDominio("Hecho inexistente")
        if actor_id not in self.actores:
            raise ErrorDominio("Actor inexistente")
        hecho = self.hechos[hecho_id]
        anterior = hecho.estado_epistemologico
        transiciones = {
            EstadoEpistemologico.NO_ACREDITADO: {EstadoEpistemologico.DECLARADO},
            EstadoEpistemologico.DECLARADO: {
                EstadoEpistemologico.CONTRASTADO_PARCIALMENTE,
                EstadoEpistemologico.CONTRADICHO,
                EstadoEpistemologico.RECHAZADO,
            },
            EstadoEpistemologico.CONTRASTADO_PARCIALMENTE: {
                EstadoEpistemologico.ACREDITADO,
                EstadoEpistemologico.CONTRADICHO,
                EstadoEpistemologico.RECHAZADO,
            },
            EstadoEpistemologico.ACREDITADO: {EstadoEpistemologico.RECTIFICADO, EstadoEpistemologico.CONTRADICHO},
            EstadoEpistemologico.CONTRADICHO: {EstadoEpistemologico.CONTRASTADO_PARCIALMENTE},
        }
        if nuevo not in transiciones.get(anterior, set()) and nuevo != anterior:
            raise ErrorDominio(f"Transición inválida: {anterior.value} -> {nuevo.value}")
        hecho.estado_epistemologico = nuevo
        self._registrar_evento("ESTADO_EPISTEMICO_CAMBIADO", hecho_id, actor_id, ahora,
                              anterior.value, nuevo.value, motivo, evidencia_ids,
                              {"nuevo_estado": nuevo.value})
        return hecho

    def registrar_fuente(self, fuente: Fuente, actor_id: str, ahora: datetime) -> Fuente:
        if actor_id not in self.actores:
            raise ErrorDominio("Actor inexistente")
        if fuente.fuente_id in self.fuentes:
            raise ErrorDominio("Fuente duplicada")
        self.fuentes[fuente.fuente_id] = fuente
        self._registrar_evento("FUENTE_REGISTRADA", fuente.fuente_id, actor_id, ahora,
                              None, fuente.__dict__, "Registro de fuente")
        return fuente

    def registrar_evidencia(self, evidencia: Evidencia, actor_id: str) -> Evidencia:
        if evidencia.evidencia_id in self.evidencias:
            raise ErrorDominio("Evidencia duplicada")
        if evidencia.fuente_id not in self.fuentes:
            raise ErrorDominio("Fuente inexistente")
        if actor_id not in self.actores:
            raise ErrorDominio("Actor inexistente")
        self.evidencias[evidencia.evidencia_id] = evidencia
        self._registrar_evento("EVIDENCIA_RECIBIDA", evidencia.evidencia_id, actor_id,
                              evidencia.recibida_en, None, evidencia.__dict__,
                              "Recepción de evidencia", (evidencia.fuente_id,))
        return evidencia

    def asociar_evidencia(self, hecho_id: str, evidencia_id: str, relacion: str,
                          fundamento: str, actor_id: str, ahora: datetime) -> ValoracionEvidencia:
        if hecho_id not in self.hechos:
            raise ErrorDominio("Hecho inexistente")
        if evidencia_id not in self.evidencias:
            raise ErrorDominio("Evidencia inexistente")
        evidencia = self.evidencias[evidencia_id]
        valoracion = ValoracionEvidencia(
            evidencia_id=evidencia_id,
            hecho_id=hecho_id,
            relacion=relacion,
            integridad=evidencia.integridad,
            autenticidad=evidencia.autenticidad,
            veracidad=evidencia.veracidad,
            fundamento=fundamento,
            valorado_en=ahora,
        )
        clave = (hecho_id, evidencia_id)
        self.heuristic_evidencias[clave] = valoracion
        self._registrar_evento("EVIDENCIA_ASOCIADA", hecho_id, actor_id, ahora,
                              None, valoracion.__dict__, fundamento,
                              (evidencia_id,), {"relacion": relacion})
        return valoracion

    def registrar_criterio(self, criterio: Criterio, actor_id: str) -> Criterio:
        if criterio.criterio_id in self.criterios:
            raise ErrorDominio("Criterio duplicado")
        if actor_id not in self.actores:
            raise ErrorDominio("Actor inexistente")
        self.criterios[criterio.criterio_id] = criterio
        self._registrar_evento("CRITERIO_REGISTRADO", criterio.criterio_id, actor_id,
                              criterio.vigente_desde, None, criterio.__dict__,
                              "Registro de criterio")
        return criterio

    def proponer_interpretacion(self, interpretacion: Interpretacion, actor_id: str) -> Interpretacion:
        if interpretacion.hecho_id not in self.hechos:
            raise ErrorDominio("Hecho inexistente")
        for evidencia_id in interpretacion.evidencia_ids:
            if evidencia_id not in self.evidencias:
                raise ErrorDominio(f"Evidencia inexistente: {evidencia_id}")
        for criterio_id in interpretacion.criterio_ids:
            if criterio_id not in self.criterios:
                raise ErrorDominio(f"Criterio inexistente: {criterio_id}")
        if interpretacion.interpretacion_id in self.interpretaciones:
            raise ErrorDominio("Interpretación duplicada")
        self.interpretaciones[interpretacion.interpretacion_id] = interpretacion
        self._registrar_evento("INTERPRETACION_PROPUESTA", interpretacion.interpretacion_id,
                              actor_id, interpretacion.propuesta_en, None,
                              interpretacion.__dict__, "Propuesta de interpretación",
                              (interpretacion.hecho_id, *interpretacion.evidencia_ids,
                               *interpretacion.criterio_ids))
        return interpretacion

    def otorgar_autorizacion(self, autorizacion: Autorizacion) -> Autorizacion:
        if autorizacion.autorizacion_id in self.autorizaciones:
            raise ErrorDominio("Autorización duplicada")
        if autorizacion.actor_id not in self.actores:
            raise ErrorDominio("Actor inexistente")
        self.autorizaciones[autorizacion.autorizacion_id] = autorizacion
        self._registrar_evento("AUTORIZACION_OTORGADA", autorizacion.autorizacion_id,
                              autorizacion.actor_id, autorizacion.otorgada_en,
                              None, autorizacion.__dict__, "Autorización otorgada")
        return autorizacion

    def adoptar_decision(self, decision: Decision) -> Decision:
        if decision.decision_id in self.decisiones:
            raise ErrorDominio("Decisión duplicada")
        if decision.actor_id not in self.actores:
            raise ErrorDominio("Actor inexistente")
        if decision.interpretacion_adoptada_id not in self.interpretaciones:
            raise ErrorDominio("Interpretación inexistente")
        if decision.autorizacion_id:
            if decision.autorizacion_id not in self.autorizaciones:
                raise ErrorDominio("Autorización inexistente")
        for evidencia_id in decision.evidencia_ids:
            if evidencia_id not in self.evidencias:
                raise ErrorDominio("Evidencia inexistente")
        for criterio_id in decision.criterio_ids:
            if criterio_id not in self.criterios:
                raise ErrorDominio("Criterio inexistente")
        interpretacion = self.interpretaciones[decision.interpretacion_adoptada_id]
        interpretacion.estado = EstadoInterpretacion.ADOPTADA
        decision.estado = EstadoDecision.ADOPTADA
        self.decisiones[decision.decision_id] = decision
        self._registrar_evento("DECISION_ADOPTADA", decision.decision_id, decision.actor_id,
                              decision.decidida_en, "PROPUESTA", "ADOPTADA",
                              decision.motivo,
                              (decision.interpretacion_adoptada_id,
                               *decision.interpretaciones_descartadas,
                               *decision.evidencia_ids,
                               *decision.criterio_ids))
        return decision

    def crear_representacion(self, representacion: RepresentacionContable,
                             actor_id: str) -> RepresentacionContable:
        if representacion.representacion_id in self.representaciones:
            raise ErrorDominio("Representación duplicada")
        if actor_id not in self.actores:
            raise ErrorDominio("Actor inexistente")
        if representacion.interpretacion_id not in self.interpretaciones:
            raise ErrorDominio("Interpretación inexistente")
        if representacion.decision_id not in self.decisiones:
            raise ErrorDominio("Decisión inexistente")
        for hecho_id in representacion.hecho_ids:
            if hecho_id not in self.hechos:
                raise ErrorDominio("Hecho inexistente")
        if not representacion.lineas:
            raise ErrorDominio("Representación sin líneas")
        if not representacion.cuadra():
            raise ErrorDominio("Asiento descuadrado")
        representacion.estado = EstadoRepresentacion.REGISTRADA
        self.representaciones[representacion.representacion_id] = representacion
        self._registrar_evento("REPRESENTACION_REGISTRADA", representacion.representacion_id,
                              actor_id, representacion.fecha_contable,
                              "PROPUESTA", "REGISTRADA",
                              "Registro de representación contable",
                              (*representacion.hecho_ids,
                               representacion.interpretacion_id,
                               representacion.decision_id,
                               *representacion.criterio_ids))
        return representacion

    def crear_rectificacion(self, rectificacion: Rectificacion,
                            actor_id: str) -> Rectificacion:
        if rectificacion.rectificacion_id in self.rectificaciones:
            raise ErrorDominio("Rectificación duplicada")
        if rectificacion.representacion_original_id not in self.representaciones:
            raise ErrorDominio("Representación original inexistente")
        if rectificacion.representacion_nueva_id not in self.representaciones:
            raise ErrorDominio("Representación nueva inexistente")
        if rectificacion.actor_id != actor_id:
            raise ErrorDominio("El actor registrado no coincide con el ejecutor")
        if rectificacion.autorizacion_id:
            if rectificacion.autorizacion_id not in self.autorizaciones:
                raise ErrorDominio("Autorización inexistente")
        original = self.representaciones[rectificacion.representacion_original_id]
        nueva = self.representaciones[rectificacion.representacion_nueva_id]
        anterior = original.estado
        original.estado = EstadoRepresentacion.RECTIFICADA
        nueva.estado = EstadoRepresentacion.REGISTRADA
        self.rectificaciones[rectificacion.rectificacion_id] = rectificacion
        self._registrar_evento("RECTIFICACION_REGISTRADA", rectificacion.rectificacion_id,
                              actor_id, rectificacion.creada_en,
                              anterior.value, nueva.estado.value,
                              rectificacion.motivo,
                              (rectificacion.representacion_original_id,
                               rectificacion.representacion_nueva_id))
        return rectificacion

    def verificar_cadena(self) -> dict[str, Any]:
        roturas: list[dict[str, Any]] = []
        previo = "0" * 64
        for indice, evento in enumerate(self.eventos, 1):
            canonico = {
                "tipo": evento.tipo,
                "objeto_id": evento.objeto_id,
                "actor_id": evento.actor_id,
                "timestamp": evento.timestamp.isoformat(),
                "motivo": evento.motivo,
                "referencias": list(evento.referencia_ids),
                "payload": evento.payload,
            }
            huella = hashlib.sha256(
                json.dumps(canonico, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
            ).hexdigest()
            valor = hashlib.sha256(f"{previo}|{huella}|{indice}".encode("utf-8")).hexdigest()
            if getattr(evento, "hash_previo", None) != previo:
                roturas.append({"tipo": "hash_previo", "evento_id": evento.evento_id})
            if getattr(evento, "huella", None) != huella:
                roturas.append({"tipo": "huella", "evento_id": evento.evento_id})
            if getattr(evento, "hash", None) != valor:
                roturas.append({"tipo": "hash", "evento_id": evento.evento_id})
            previo = getattr(evento, "hash", previo)
        return {"cadena_valida": len(roturas) == 0, "total": len(self.eventos), "roturas": roturas}

    def reconstruir(self, fecha_epistemica: datetime) -> dict[str, Any]:
        hechos: list[dict[str, Any]] = []
        for hecho in self.hechos.values():
            if hecho.registrado_en <= fecha_epistemica:
                hechos.append({
                    "hecho_id": hecho.hecho_id,
                    "tipo": hecho.tipo,
                    "estado_epistemologico": hecho.estado_epistemologico.value,
                    "estado_economico": hecho.estado_economico,
                    "incertidumbre": hecho.incertidumbre,
                })

        interpretaciones = {
            interpretacion.interpretacion_id: {
                "estado": interpretacion.estado.value,
                "tipo": interpretacion.tipo,
                "criterios": interpretacion.criterio_ids,
            }
            for interpretacion in self.interpretaciones.values()
            if interpretacion.propuesta_en <= fecha_epistemica
        }
        decisiones = {
            decision.decision_id: {
                "estado": decision.estado.value,
                "interpretacion": decision.interpretacion_adoptada_id,
            }
            for decision in self.decisiones.values()
            if decision.decidida_en <= fecha_epistemica
        }
        representaciones = {
            representacion.representacion_id: {
                "estado": representacion.estado.value,
                "decision": representacion.decision_id,
                "cuadra": representacion.cuadra(),
            }
            for representacion in self.representaciones.values()
            if representacion.fecha_contable <= fecha_epistemica
        }
        evidencias = {
            evidencia_id: {
                "integridad": evidencia.integridad,
                "autenticidad": evidencia.autenticidad,
                "veracidad": evidencia.veracidad,
            }
            for evidencia_id, evidencia in self.evidencias.items()
            if evidencia.recibida_en <= fecha_epistemica
        }
        return {
            "fecha_epistemica": fecha_epistemica.isoformat(),
            "hechos": hechos,
            "evidencias": evidencias,
            "interpretaciones": interpretaciones,
            "decisiones": decisiones,
            "representaciones": representaciones,
            "eventos_disponibles": sum(1 for e in self.eventos if e.timestamp <= fecha_epistemica),
        }
