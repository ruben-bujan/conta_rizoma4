"""Servicios de dominio promovidos desde la POC.

No contiene persistencia ni dependencias de FastAPI, PostgreSQL, JWT o RIZOMA4.
"""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import fields, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Iterable, Optional

from ..excepciones import ErrorDominio
from ..entidades.economicas import EntidadContable, EstadoEpistemologico, EjercicioContable, HechoEconomico
from ..entidades.epistemicas import (
    Criterio,
    EstadoInterpretacion,
    Evidencia,
    Fuente,
    Interpretacion,
    ValoracionEvidencia,
)
from ..entidades.contables import (
    Actor,
    AlertaImporte,
    Autorizacion,
    CalificacionEntidad,
    CierreContable,
    CriticidadImporte,
    Decision,
    EstadoDecision,
    EstadoRepresentacion,
    Evento,
    InformeAdmin,
    Linea,
    ModoContabilidad,
    PermisoConcedido,
    Rectificacion,
    RemisionInvestigacion,
    RepresentacionContable,
    RegistroNoAsiento,
    Rol,
    SolicitudAdmin,
)


def _normalizar_json(valor: Any) -> Any:
    """Convierte snapshots del dominio a una forma estable y serializable."""
    if isinstance(valor, Enum):
        return _normalizar_json(valor.value)
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    if isinstance(valor, Decimal):
        return str(valor)
    if is_dataclass(valor):
        return {campo.name: _normalizar_json(getattr(valor, campo.name)) for campo in fields(valor)}
    if isinstance(valor, dict):
        return {str(clave): _normalizar_json(contenido) for clave, contenido in valor.items()}
    if isinstance(valor, (tuple, list)):
        return [_normalizar_json(elemento) for elemento in valor]
    if isinstance(valor, set):
        return sorted((_normalizar_json(elemento) for elemento in valor), key=repr)
    if valor is None or isinstance(valor, (str, int, float, bool)):
        return valor
    raise TypeError(f"Tipo no serializable en evento de dominio: {type(valor).__name__}")


_MATRIZ_COMPETENCIAS_ROL: dict[str, Rol] = {
    "DECISION": Rol.JEFE_CONTABILIDAD,
    "REPRESENTACION": Rol.JEFE_CONTABILIDAD,
    "ASIENTO_DIARIO": Rol.JEFE_CONTABILIDAD,
    "RECTIFICACION": Rol.JEFE_CONTABILIDAD,
    "CIERRE_EJERCICIO": Rol.SUBDIRECTOR,
    "REAPERTURA_EJERCICIO": Rol.SUBDIRECTOR,
}


class NucleoEpistemicoContable:
    def __init__(self) -> None:
        self.entidades: dict[str, EntidadContable] = {}
        self.actores: dict[str, Actor] = {}
        self.fuentes: dict[str, Fuente] = {}
        self.evidencias: dict[str, Evidencia] = {}
        self.valoraciones_evidencia: dict[tuple[str, str], ValoracionEvidencia] = {}
        self.hechos: dict[str, HechoEconomico] = {}
        self.criterios: dict[str, Criterio] = {}
        self.interpretaciones: dict[str, Interpretacion] = {}
        self.autorizaciones: dict[str, Autorizacion] = {}
        self.decisiones: dict[str, Decision] = {}
        self.representaciones: dict[str, RepresentacionContable] = {}
        self.rectificaciones: dict[str, Rectificacion] = {}
        self.ejercicios: dict[str, EjercicioContable] = {}
        self.cierres: list[CierreContable] = []
        self.eventos: list[Evento] = []
        self.permisos: dict[str, PermisoConcedido] = {}
        self.solicitudes_admin: dict[str, SolicitudAdmin] = {}
        self.informes_admin: dict[str, InformeAdmin] = {}
        self.remisiones: dict[str, RemisionInvestigacion] = {}
        self.alertas_importe: dict[str, AlertaImporte] = {}
        self.registros_no_asiento: dict[str, RegistroNoAsiento] = {}
        self.modos_entidad: dict[str, ModoContabilidad] = {}
        self.calificaciones_entidad: dict[str, dict[CalificacionEntidad, bool]] = {}
        self.beneficio_industrial_anterior: dict[str, int] = {}

    def _validar_fecha_evento(self, timestamp: datetime) -> None:
        if not isinstance(timestamp, datetime):
            raise ErrorDominio("El evento requiere fecha y hora de registro")
        if not self.eventos:
            return
        anterior = self.eventos[-1].timestamp
        if (timestamp.tzinfo is None) != (anterior.tzinfo is None):
            raise ErrorDominio("No se pueden mezclar fechas con y sin zona horaria en el ledger")
        if timestamp < anterior:
            raise ErrorDominio("No se permite registrar un evento con fecha anterior al último evento")

    def _ejercicio_para(self, entidad_id: str | None, momento: datetime) -> str | None:
        if entidad_id is None:
            return None
        for ejercicio in self.ejercicios.values():
            if (
                ejercicio.entidad_id == entidad_id
                and ejercicio.inicio <= momento <= ejercicio.fin
            ):
                return ejercicio.ejercicio_id
        return None

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
        self._validar_fecha_evento(timestamp)
        referencias = tuple(referencia_ids)
        payload_copiado = deepcopy(payload or {})
        previo = getattr(self.eventos[-1], "hash", "0" * 64) if self.eventos else "0" * 64
        numero = len(self.eventos) + 1
        canonico = {
            "tipo": tipo,
            "objeto_id": objeto_id,
            "actor_id": actor_id,
            "timestamp": timestamp.isoformat(),
            "motivo": motivo,
            "referencias": list(referencias),
            "estado_anterior": _normalizar_json(anterior),
            "estado_posterior": _normalizar_json(posterior),
            "payload": _normalizar_json(payload_copiado),
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
            referencia_ids=referencias,
            payload=payload_copiado,
        )
        evento.hash = valor
        evento.huella = huella
        evento.hash_previo = previo
        evento.indice = numero
        self.eventos.append(evento)
        return evento

    def registrar_ejercicio(
        self, ejercicio: EjercicioContable, actor_id: str, registrado_en: datetime
    ) -> EjercicioContable:
        self._validar_fecha_evento(registrado_en)
        if ejercicio.ejercicio_id in self.ejercicios:
            raise ErrorDominio("Ejercicio duplicado")
        if actor_id not in self.actores:
            raise ErrorDominio("Actor inexistente")
        if ejercicio.estado != "ABIERTO":
            raise ErrorDominio("El ejercicio debe registrarse inicialmente abierto")
        self.ejercicios[ejercicio.ejercicio_id] = ejercicio
        self._registrar_evento(
            "EJERCICIO_REGISTRADO", ejercicio.ejercicio_id, actor_id, registrado_en,
            None, "ABIERTO", "Registro de ejercicio contable",
            (ejercicio.entidad_id,),
            {"entidad_id": ejercicio.entidad_id, "inicio": ejercicio.inicio.isoformat(),
             "fin": ejercicio.fin.isoformat()},
        )
        return ejercicio

    def registrar_cierre_ejercicio(
        self, cierre: CierreContable, actor_id: str, autorizacion_id: str, motivo: str
    ) -> CierreContable:
        self._validar_fecha_evento(cierre.registrado_en)
        ejercicio = self.ejercicios.get(cierre.ejercicio_id)
        if ejercicio is None:
            raise ErrorDominio("Ejercicio no registrado en el núcleo")
        if actor_id not in self.actores:
            raise ErrorDominio("Actor inexistente")
        self.verificar_competencia(
            actor_id, "CIERRE_EJERCICIO", cierre.ejercicio_id, cierre.registrado_en,
        )
        autorizacion = self.autorizaciones.get(autorizacion_id)
        if autorizacion is None:
            raise ErrorDominio("Autorización de cierre inexistente")
        self._validar_autorizacion(autorizacion, cierre.registrado_en)
        if autorizacion.actor_id not in self.actores:
            raise ErrorDominio("Actor autorizador inexistente")
        if autorizacion.competencia != "CIERRE_EJERCICIO" or autorizacion.alcance != ejercicio.ejercicio_id:
            raise ErrorDominio("La autorización no cubre este cierre")
        if autorizacion.actor_id == actor_id:
            raise ErrorDominio("El responsable del cierre no puede autorizar su propio cierre")
        if autorizacion.otorgada_en > cierre.registrado_en:
            raise ErrorDominio("La autorización se otorgó después del cierre registrado")
        if not motivo:
            raise ErrorDominio("El cierre requiere motivo")
        if cierre.fecha_cierre < ejercicio.fin:
            raise ErrorDominio("La fecha de cierre precede al fin del ejercicio")
        if cierre.registrado_en < cierre.fecha_cierre:
            raise ErrorDominio("El cierre no puede registrarse antes de su fecha contable")
        if ejercicio.estado not in {"ABIERTO", "REABIERTO"}:
            raise ErrorDominio("Sólo puede cerrarse un ejercicio abierto o reabierto")
        if any(c.cierre_id == cierre.cierre_id for c in self.cierres):
            raise ErrorDominio("Identificador de cierre duplicado")
        if any(rid not in self.representaciones for rid in cierre.representacion_ids):
            raise ErrorDominio("El cierre referencia representaciones no registradas")

        anterior = ejercicio.estado
        ejercicio.estado = "CERRADO"
        self.cierres.append(cierre)
        self._registrar_evento(
            "EJERCICIO_CERRADO", ejercicio.ejercicio_id, actor_id, cierre.registrado_en,
            anterior, "CERRADO", motivo,
            (autorizacion_id, cierre.cierre_id, *cierre.representacion_ids),
            {"cierre_id": cierre.cierre_id, "fecha_cierre": cierre.fecha_cierre.isoformat(),
             "representacion_ids": list(cierre.representacion_ids),
             "autorizacion_id": autorizacion_id,
             "resultado_ejercicio": cierre.resultado_ejercicio,
             "regularizacion": [self._linea_a_dict(l) for l in cierre.regularizacion],
             "asiento_cierre": [self._linea_a_dict(l) for l in cierre.asiento_cierre],
             "asiento_apertura": [self._linea_a_dict(l) for l in cierre.asiento_apertura]},
        )
        return cierre

    def registrar_reapertura_ejercicio(
        self, ejercicio_id: str, actor_id: str, autorizacion_id: str,
        motivo: str, registrada_en: datetime,
    ) -> EjercicioContable:
        self._validar_fecha_evento(registrada_en)
        ejercicio = self.ejercicios.get(ejercicio_id)
        if ejercicio is None:
            raise ErrorDominio("Ejercicio no registrado en el núcleo")
        if actor_id not in self.actores:
            raise ErrorDominio("Actor inexistente")
        self.verificar_competencia(
            actor_id, "REAPERTURA_EJERCICIO", ejercicio_id, registrada_en,
        )
        autorizacion = self.autorizaciones.get(autorizacion_id)
        if autorizacion is None:
            raise ErrorDominio("Autorización de reapertura inexistente")
        self._validar_autorizacion(autorizacion, registrada_en)
        if autorizacion.actor_id not in self.actores:
            raise ErrorDominio("Actor autorizador inexistente")
        if autorizacion.competencia != "REAPERTURA_EJERCICIO" or autorizacion.alcance != ejercicio_id:
            raise ErrorDominio("La autorización no cubre esta reapertura")
        if autorizacion.actor_id == actor_id:
            raise ErrorDominio("El responsable de la reapertura no puede autorizarla")
        if autorizacion.otorgada_en > registrada_en:
            raise ErrorDominio("La autorización se otorgó después de la reapertura")
        if not motivo:
            raise ErrorDominio("La reapertura requiere motivo")
        if ejercicio.estado != "CERRADO":
            raise ErrorDominio("Sólo puede reabrirse un ejercicio cerrado")
        cierre = next((c for c in reversed(self.cierres) if c.ejercicio_id == ejercicio_id), None)
        if cierre is None or registrada_en <= cierre.registrado_en:
            raise ErrorDominio("La reapertura debe ser posterior al cierre")
        ejercicio.estado = "REABIERTO"
        self._registrar_evento(
            "EJERCICIO_REABIERTO", ejercicio_id, actor_id, registrada_en,
            "CERRADO", "REABIERTO", motivo,
            (autorizacion_id, cierre.cierre_id),
            {"cierre_id": cierre.cierre_id},
        )
        return ejercicio

    @staticmethod
    def _linea_a_dict(linea) -> dict[str, Any]:
        return {"cuenta": linea.cuenta, "debe": linea.debe, "haber": linea.haber}

    def registrar_entidad(self, entidad: EntidadContable, actor_id: str, ahora: datetime) -> EntidadContable:
        self._validar_fecha_evento(ahora)
        if entidad.entidad_id in self.entidades:
            raise ErrorDominio("Entidad duplicada")
        if actor_id not in self.actores:
            raise ErrorDominio("Actor inexistente")
        self.entidades[entidad.entidad_id] = entidad
        self._registrar_evento("ENTIDAD_REGISTRADA", entidad.entidad_id, actor_id, ahora,
                              None, entidad.__dict__, "Alta de entidad")
        return entidad

    def registrar_actor(self, actor: Actor, ahora: datetime) -> Actor:
        self._validar_fecha_evento(ahora)
        if actor.actor_id in self.actores:
            raise ErrorDominio("Actor duplicado")
        self.actores[actor.actor_id] = actor
        self._registrar_evento("ACTOR_REGISTRADO", actor.actor_id, actor.actor_id, ahora,
                              None, actor.__dict__, "Alta de actor")
        return actor

    def registrar_hecho(self, hecho: HechoEconomico, actor_id: str) -> HechoEconomico:
        self._validar_fecha_evento(hecho.registrado_en)
        if hecho.hecho_id in self.hechos:
            raise ErrorDominio("Hecho duplicado")
        if hecho.entidad_id not in self.entidades:
            raise ErrorDominio("Entidad inexistente")
        if actor_id not in self.actores:
            raise ErrorDominio("Actor inexistente")
        self.hechos[hecho.hecho_id] = hecho
        anterior = None
        posterior = hecho.estado_epistemologico.value
        self._registrar_evento("HECHO_REGISTRADO", hecho.hecho_id, actor_id,
                              hecho.registrado_en, anterior, posterior,
                              "Registro inicial del hecho", (hecho.entidad_id,),
                              {"tipo": hecho.tipo, "estado_economico": hecho.estado_economico,
                               "hecho": _normalizar_json(hecho)})
        return hecho

    def relacionar_hechos(self, origen: str, destino: str, relacion: str,
                          actor_id: str, ahora: datetime, motivo: str) -> None:
        self._validar_fecha_evento(ahora)
        if actor_id not in self.actores:
            raise ErrorDominio("Actor inexistente")
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
        self._validar_fecha_evento(ahora)
        if hecho_id not in self.hechos:
            raise ErrorDominio("Hecho inexistente")
        hecho = self.hechos[hecho_id]
        if actor_id not in self.actores:
            raise ErrorDominio("Actor inexistente")
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
            EstadoEpistemologico.ACREDITADO: {
                EstadoEpistemologico.RECTIFICADO,
                EstadoEpistemologico.CONTRADICHO,
            },
            EstadoEpistemologico.CONTRADICHO: {
                EstadoEpistemologico.CONTRASTADO_PARCIALMENTE,
            },
        }
        if nuevo not in transiciones.get(anterior, set()) and nuevo != anterior:
            raise ErrorDominio(f"Transición inválida: {anterior.value} -> {nuevo.value}")
        hecho.estado_epistemologico = nuevo
        self._registrar_evento("ESTADO_EPISTEMICO_CAMBIADO", hecho_id, actor_id, ahora,
                              anterior.value, nuevo.value, motivo, evidencia_ids,
                              {"nuevo_estado": nuevo.value})
        return hecho

    def registrar_fuente(self, fuente: Fuente, actor_id: str, ahora: datetime) -> Fuente:
        self._validar_fecha_evento(ahora)
        if actor_id not in self.actores:
            raise ErrorDominio("Actor inexistente")
        if fuente.fuente_id in self.fuentes:
            raise ErrorDominio("Fuente duplicada")
        self.fuentes[fuente.fuente_id] = fuente
        self._registrar_evento("FUENTE_REGISTRADA", fuente.fuente_id, actor_id, ahora,
                              None, fuente.__dict__, "Registro de fuente")
        return fuente

    def registrar_evidencia(self, evidencia: Evidencia, actor_id: str) -> Evidencia:
        if evidencia.registrada_en is None:
            raise ErrorDominio("La evidencia requiere fecha y hora de registro")
        self._validar_fecha_evento(evidencia.registrada_en)
        if evidencia.evidencia_id in self.evidencias:
            raise ErrorDominio("Evidencia duplicada")
        if evidencia.fuente_id not in self.fuentes:
            raise ErrorDominio("Fuente inexistente")
        if actor_id not in self.actores:
            raise ErrorDominio("Actor inexistente")
        if evidencia.registrada_en < evidencia.recibida_en:
            raise ErrorDominio("La evidencia no puede registrarse antes de recibirse")
        self.evidencias[evidencia.evidencia_id] = evidencia
        self._registrar_evento("EVIDENCIA_RECIBIDA", evidencia.evidencia_id, actor_id,
                              evidencia.registrada_en, None, evidencia.__dict__,
                              "Recepción de evidencia", (evidencia.fuente_id,))
        return evidencia

    def asociar_evidencia(self, hecho_id: str, evidencia_id: str, relacion: str,
                          fundamento: str, actor_id: str, ahora: datetime) -> ValoracionEvidencia:
        self._validar_fecha_evento(ahora)
        if actor_id not in self.actores:
            raise ErrorDominio("Actor inexistente")
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
        self.valoraciones_evidencia[(hecho_id, evidencia_id)] = valoracion
        self._registrar_evento("EVIDENCIA_ASOCIADA", hecho_id, actor_id, ahora,
                              None, valoracion.__dict__, fundamento,
                              (evidencia_id,), {"relacion": relacion})
        return valoracion

    def registrar_criterio(self, criterio: Criterio, actor_id: str) -> Criterio:
        if criterio.registrado_en is None:
            raise ErrorDominio("El criterio requiere fecha y hora de registro")
        self._validar_fecha_evento(criterio.registrado_en)
        if criterio.criterio_id in self.criterios:
            raise ErrorDominio("Criterio duplicado")
        if actor_id not in self.actores:
            raise ErrorDominio("Actor inexistente")
        self.criterios[criterio.criterio_id] = criterio
        self._registrar_evento("CRITERIO_REGISTRADO", criterio.criterio_id, actor_id,
                              criterio.registrado_en, None, criterio.__dict__,
                              "Registro de criterio")
        return criterio

    def proponer_interpretacion(self, interpretacion: Interpretacion, actor_id: str) -> Interpretacion:
        self._validar_fecha_evento(interpretacion.propuesta_en)
        if actor_id not in self.actores:
            raise ErrorDominio("Actor inexistente")
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
        self._validar_fecha_evento(autorizacion.otorgada_en)
        if autorizacion.vigente_hasta is not None and autorizacion.vigente_hasta < autorizacion.otorgada_en:
            raise ErrorDominio("La vigencia no puede terminar antes del otorgamiento")
        if autorizacion.autorizacion_id in self.autorizaciones:
            raise ErrorDominio("Autorización duplicada")
        if autorizacion.actor_id not in self.actores:
            raise ErrorDominio("Actor inexistente")
        self.autorizaciones[autorizacion.autorizacion_id] = autorizacion
        self._registrar_evento("AUTORIZACION_OTORGADA", autorizacion.autorizacion_id,
                              autorizacion.actor_id, autorizacion.otorgada_en,
                              None, autorizacion.__dict__, "Autorización otorgada")
        return autorizacion

    def revocar_autorizacion(
        self, autorizacion_id: str, actor_id: str, motivo: str, revocada_en: datetime
    ) -> Autorizacion:
        self._validar_fecha_evento(revocada_en)
        autorizacion = self.autorizaciones.get(autorizacion_id)
        if autorizacion is None:
            raise ErrorDominio("Autorización inexistente")
        if actor_id not in self.actores:
            raise ErrorDominio("Actor inexistente")
        if actor_id != autorizacion.actor_id:
            raise ErrorDominio("Sólo quien otorgó la autorización puede revocarla")
        if autorizacion.revocada_en is not None:
            raise ErrorDominio("La autorización ya está revocada")
        if revocada_en < autorizacion.otorgada_en:
            raise ErrorDominio("La revocación precede al otorgamiento")
        if not motivo.strip():
            raise ErrorDominio("La revocación requiere motivo")
        anterior = _normalizar_json(autorizacion)
        autorizacion.revocada_en = revocada_en
        autorizacion.revocada_por = actor_id
        autorizacion.motivo_revocacion = motivo.strip()
        self._registrar_evento(
            "AUTORIZACION_REVOCADA", autorizacion_id, actor_id, revocada_en,
            anterior, _normalizar_json(autorizacion), motivo.strip(), (autorizacion_id,),
        )
        return autorizacion

    @staticmethod
    def _validar_autorizacion(autorizacion: Autorizacion, cuando: datetime) -> None:
        if autorizacion.revocada_en is not None and autorizacion.revocada_en <= cuando:
            raise ErrorDominio("La autorización estaba revocada en la fecha del acto")
        if autorizacion.otorgada_en > cuando:
            raise ErrorDominio("La autorización se otorgó después del acto")
        if autorizacion.vigente_hasta is not None and cuando > autorizacion.vigente_hasta:
            raise ErrorDominio("La autorización había caducado en la fecha del acto")

    def adoptar_decision(self, decision: Decision) -> Decision:
        self._validar_fecha_evento(decision.decidida_en)
        if decision.decision_id in self.decisiones:
            raise ErrorDominio("Decisión duplicada")
        if decision.actor_id not in self.actores:
            raise ErrorDominio("Actor inexistente")
        hecho = self.hechos.get(decision.objeto_id)
        self.verificar_competencia(
            decision.actor_id, "DECISION",
            self._ejercicio_para(hecho.entidad_id if hecho else None, decision.decidida_en),
            decision.decidida_en,
        )
        if decision.interpretacion_adoptada_id not in self.interpretaciones:
            raise ErrorDominio("Interpretación inexistente")
        if decision.autorizacion_id not in self.autorizaciones:
            raise ErrorDominio("Autorización inexistente")
        for evidencia_id in decision.evidencia_ids:
            if evidencia_id not in self.evidencias:
                raise ErrorDominio("Evidencia inexistente")
        for criterio_id in decision.criterio_ids:
            if criterio_id not in self.criterios:
                raise ErrorDominio("Criterio inexistente")
        interpretacion = self.interpretaciones[decision.interpretacion_adoptada_id]
        if decision.objeto_id != interpretacion.hecho_id:
            raise ErrorDominio("La decisión debe corresponder al hecho de la interpretación adoptada")
        if interpretacion.estado not in {EstadoInterpretacion.PROPUESTA, EstadoInterpretacion.EVALUADA}:
            raise ErrorDominio("La interpretación ya fue adoptada, descartada o revocada")
        if decision.interpretacion_adoptada_id in decision.interpretaciones_descartadas:
            raise ErrorDominio("Una interpretación no puede adoptarse y descartarse a la vez")
        alternativas = []
        for interpretacion_id in decision.interpretaciones_descartadas:
            alternativa = self.interpretaciones.get(interpretacion_id)
            if alternativa is None:
                raise ErrorDominio(f"Interpretación descartada inexistente: {interpretacion_id}")
            if alternativa.hecho_id != decision.objeto_id:
                raise ErrorDominio("Las interpretaciones descartadas deben corresponder al mismo hecho")
            if alternativa.estado not in {EstadoInterpretacion.PROPUESTA, EstadoInterpretacion.EVALUADA}:
                raise ErrorDominio("La interpretación alternativa ya fue resuelta")
            alternativas.append(alternativa)
        if decision.autorizacion_id:
            autorizacion = self.autorizaciones[decision.autorizacion_id]
            self._validar_autorizacion(autorizacion, decision.decidida_en)
            if autorizacion.alcance not in {decision.objeto_id, decision.interpretacion_adoptada_id}:
                raise ErrorDominio("La autorización no cubre el objeto de la decisión")
            if autorizacion.otorgada_en > decision.decidida_en:
                raise ErrorDominio("La autorización se otorgó después de la decisión")
            if autorizacion.actor_id == decision.actor_id:
                raise ErrorDominio("El decisor no puede autorizar su propia decisión")
        interpretacion.estado = EstadoInterpretacion.ADOPTADA
        for alternativa in alternativas:
            alternativa.estado = EstadoInterpretacion.DESCARTADA
        decision.estado = EstadoDecision.ADOPTADA
        self.decisiones[decision.decision_id] = decision
        self._registrar_evento("DECISION_ADOPTADA", decision.decision_id, decision.actor_id,
                              decision.decidida_en, EstadoDecision.PROPUESTA,
                              _normalizar_json(decision),
                              decision.motivo,
                              (decision.interpretacion_adoptada_id,
                               *decision.interpretaciones_descartadas,
                               *decision.evidencia_ids,
                               *decision.criterio_ids),
                              {"interpretaciones_estado": {
                                  decision.interpretacion_adoptada_id: EstadoInterpretacion.ADOPTADA.value,
                                  **{i.interpretacion_id: EstadoInterpretacion.DESCARTADA.value
                                     for i in alternativas},
                              }})
        return decision

    def crear_representacion(self, representacion: RepresentacionContable,
                             actor_id: str) -> RepresentacionContable:
        if representacion.registrada_en is None:
            raise ErrorDominio("La representación requiere fecha y hora de registro epistémico")
        self._validar_fecha_evento(representacion.registrada_en)
        if representacion.representacion_id in self.representaciones:
            raise ErrorDominio("Representación duplicada")
        if actor_id not in self.actores:
            raise ErrorDominio("Actor inexistente")
        hecho = (
            self.hechos.get(representacion.hecho_ids[0])
            if representacion.hecho_ids else None
        )
        alcance = self._ejercicio_para(
            hecho.entidad_id if hecho else None, representacion.registrada_en,
        )
        self.verificar_competencia(
            actor_id, "REPRESENTACION", alcance, representacion.registrada_en,
        )
        self.verificar_competencia(
            actor_id, "ASIENTO_DIARIO", alcance, representacion.registrada_en,
        )
        if representacion.interpretacion_id not in self.interpretaciones:
            raise ErrorDominio("Interpretación inexistente")
        if representacion.decision_id not in self.decisiones:
            raise ErrorDominio("Decisión inexistente")
        decision = self.decisiones[representacion.decision_id]
        if decision.estado != EstadoDecision.ADOPTADA:
            raise ErrorDominio("La representación requiere una decisión adoptada")
        autorizacion = self.autorizaciones.get(representacion.autorizacion_id)
        if autorizacion is None:
            raise ErrorDominio("Autorización de representación inexistente")
        self._validar_autorizacion(autorizacion, representacion.registrada_en)
        if decision.interpretacion_adoptada_id != representacion.interpretacion_id:
            raise ErrorDominio("La representación debe usar la interpretación adoptada por su decisión")
        if self.interpretaciones[representacion.interpretacion_id].estado != EstadoInterpretacion.ADOPTADA:
            raise ErrorDominio("La representación requiere una interpretación adoptada")
        if decision.objeto_id not in representacion.hecho_ids:
            raise ErrorDominio("La decisión no corresponde a los hechos de la representación")
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
                              actor_id, representacion.registrada_en,
                              EstadoRepresentacion.PROPUESTA,
                              _normalizar_json(representacion),
                              "Registro de representación contable",
                              (*representacion.hecho_ids,
                               representacion.interpretacion_id,
                               representacion.decision_id,
                               *representacion.criterio_ids))
        return representacion

    def crear_rectificacion(self, rectificacion: Rectificacion, actor_id: str) -> Rectificacion:
        self._validar_fecha_evento(rectificacion.creada_en)
        if actor_id not in self.actores:
            raise ErrorDominio("Actor inexistente")
        original = self.representaciones.get(rectificacion.representacion_original_id)
        hecho = (
            self.hechos.get(original.hecho_ids[0])
            if original and original.hecho_ids else None
        )
        alcance = self._ejercicio_para(
            hecho.entidad_id if hecho else None, rectificacion.creada_en,
        )
        self.verificar_competencia(
            actor_id, "RECTIFICACION", alcance, rectificacion.creada_en,
        )
        if rectificacion.rectificacion_id in self.rectificaciones:
            raise ErrorDominio("Rectificación duplicada")
        if rectificacion.representacion_original_id not in self.representaciones:
            raise ErrorDominio("Representación original inexistente")
        if rectificacion.representacion_nueva_id not in self.representaciones:
            raise ErrorDominio("Representación nueva inexistente")
        if rectificacion.actor_id != actor_id:
            raise ErrorDominio("El actor registrado no coincide con el ejecutor")
        if rectificacion.autorizacion_id:
            autorizacion = self.autorizaciones.get(rectificacion.autorizacion_id)
            if autorizacion is None:
                raise ErrorDominio("Autorización inexistente")
            self._validar_autorizacion(autorizacion, rectificacion.creada_en)
            alcance_valido = {
                rectificacion.rectificacion_id,
                rectificacion.representacion_original_id,
                rectificacion.representacion_nueva_id,
            }
            if autorizacion.alcance not in alcance_valido:
                raise ErrorDominio("La autorización no cubre esta rectificación")
            if autorizacion.otorgada_en > rectificacion.creada_en:
                raise ErrorDominio("La autorización se otorgó después de la rectificación")
            if autorizacion.actor_id == actor_id:
                raise ErrorDominio("El ejecutor no puede autorizar su propia rectificación")
        original = self.representaciones[rectificacion.representacion_original_id]
        nueva = self.representaciones[rectificacion.representacion_nueva_id]
        if original.representacion_id == nueva.representacion_id:
            raise ErrorDominio("La rectificación requiere representaciones distintas")
        if original.estado != EstadoRepresentacion.REGISTRADA:
            raise ErrorDominio("La representación original debe estar registrada y no rectificada")
        if nueva.estado != EstadoRepresentacion.REGISTRADA:
            raise ErrorDominio("La representación nueva debe estar registrada")
        if any(r.representacion_nueva_id == nueva.representacion_id for r in self.rectificaciones.values()):
            raise ErrorDominio("La representación nueva ya se usó en otra rectificación")
        if not nueva.lineas or not nueva.cuadra():
            raise ErrorDominio("La representación nueva no cuadra")
        if not rectificacion.tipo or not rectificacion.causa or not rectificacion.motivo.strip():
            raise ErrorDominio("La rectificación requiere tipo, causa y motivo")
        if rectificacion.creada_en < original.fecha_contable:
            raise ErrorDominio("La rectificación precede a la representación original")
        anterior = original.estado
        original.estado = EstadoRepresentacion.RECTIFICADA
        nueva.estado = EstadoRepresentacion.REGISTRADA
        self.rectificaciones[rectificacion.rectificacion_id] = rectificacion
        self._registrar_evento("RECTIFICACION_REGISTRADA", rectificacion.rectificacion_id,
                              actor_id, rectificacion.creada_en,
                              {"original": anterior.value, "nueva": nueva.estado.value},
                              _normalizar_json(rectificacion),
                              rectificacion.motivo,
                              (rectificacion.representacion_original_id,
                               rectificacion.representacion_nueva_id),
                              {"estados_representaciones": {
                                  rectificacion.representacion_original_id: EstadoRepresentacion.RECTIFICADA.value,
                                  rectificacion.representacion_nueva_id: EstadoRepresentacion.REGISTRADA.value,
                              }})
        return rectificacion

    # ── Permisos y competencia ──────────────────────────────────────────

    def conceder_permiso(
        self,
        permiso_id: str,
        otorgante_id: str,
        beneficiario_id: str,
        competencia: str,
        alcance: str,
        otorgada_en: datetime,
        vigente_hasta: datetime | None = None,
    ) -> PermisoConcedido:
        self._validar_fecha_evento(otorgada_en)
        if permiso_id in self.permisos:
            raise ErrorDominio("Permiso duplicado")
        if otorgante_id not in self.actores:
            raise ErrorDominio("Otorgante inexistente")
        if beneficiario_id not in self.actores:
            raise ErrorDominio("Beneficiario inexistente")
        otorgante = self.actores[otorgante_id]
        beneficiario = self.actores[beneficiario_id]
        if otorgante.rol == Rol.ADMIN:
            raise ErrorDominio("El ADMIN no puede conceder permisos de la jerarquia contable")
        if otorgante.nivel_jerarquia <= beneficiario.nivel_jerarquia:
            raise ErrorDominio("Solo un superior jerarquico puede conceder permiso")
        permiso = PermisoConcedido(
            permiso_id=permiso_id,
            otorgante_id=otorgante_id,
            beneficiario_id=beneficiario_id,
            competencia=competencia,
            alcance=alcance,
            otorgada_en=otorgada_en,
            vigente_hasta=vigente_hasta,
        )
        self.permisos[permiso_id] = permiso
        self._registrar_evento(
            "PERMISO_CONCEDIDO", permiso_id, otorgante_id, otorgada_en,
            None, permiso.__dict__, "Concesión de permiso",
            (beneficiario_id,),
            {"competencia": competencia, "alcance": alcance},
        )
        return permiso

    def revocar_permiso(
        self,
        permiso_id: str,
        actor_id: str,
        motivo: str,
        revocada_en: datetime,
    ) -> PermisoConcedido:
        self._validar_fecha_evento(revocada_en)
        permiso = self.permisos.get(permiso_id)
        if permiso is None:
            raise ErrorDominio("Permiso inexistente")
        if actor_id not in self.actores:
            raise ErrorDominio("Actor inexistente")
        if actor_id != permiso.otorgante_id:
            raise ErrorDominio("Solo quien concedió el permiso puede revocarlo")
        if permiso.revocada_en is not None:
            raise ErrorDominio("El permiso ya está revocado")
        anterior = permiso.__dict__.copy()
        permiso.revocada_en = revocada_en
        self._registrar_evento(
            "PERMISO_REVOCADO", permiso_id, actor_id, revocada_en,
            anterior, permiso.__dict__.copy(), motivo,
            (permiso_id,),
        )
        return permiso

    def verificar_competencia(
        self,
        actor_id: str,
        competencia_requerida: str,
        alcance: str | None,
        momento: datetime,
        modo: ModoContabilidad | None = None,
        grupo_pgc: str | None = None,
    ) -> None:
        actor = self.actores.get(actor_id)
        if actor is None:
            raise ErrorDominio("Actor inexistente")
        rol_minimo = _MATRIZ_COMPETENCIAS_ROL.get(competencia_requerida)
        if (
            rol_minimo is not None
            and actor.rol is not Rol.ADMIN
            and actor.puede_ejecutar(rol_minimo)
        ):
            return
        for permiso in self.permisos.values():
            if (
                permiso.beneficiario_id == actor_id
                and permiso.competencia == competencia_requerida
                and (alcance is None or permiso.alcance == alcance or permiso.alcance == "*")
                and permiso.revocada_en is None
                and permiso.otorgada_en <= momento
                and (permiso.vigente_hasta is None or momento <= permiso.vigente_hasta)
            ):
                return
        raise ErrorDominio(
            f"El actor {actor_id} no tiene competencia para {competencia_requerida} "
            f"en {alcance or 'cualquier alcance'} a {momento.isoformat()}"
        )

    def cambiar_modo_contabilidad(
        self,
        entidad_id: str,
        modo: ModoContabilidad,
        actor_id: str,
        momento: datetime,
        motivo: str,
    ) -> None:
        self._validar_fecha_evento(momento)
        if entidad_id not in self.entidades:
            raise ErrorDominio("Entidad inexistente")
        if actor_id not in self.actores:
            raise ErrorDominio("Actor inexistente")
        actor = self.actores[actor_id]
        if modo == ModoContabilidad.EXTRAORDINARIO_CRITICO and actor.rol != Rol.DIRECTOR:
            raise ErrorDominio("Solo el DIRECTOR puede activar modo extraordinario crítico")
        if modo == ModoContabilidad.EXTRAORDINARIO_NOCRITICO and actor.rol not in {Rol.SUBDIRECTOR, Rol.DIRECTOR}:
            raise ErrorDominio("Solo SUBDIRECTOR o DIRECTOR pueden activar modo extraordinario no crítico")
        anterior = self.modos_entidad.get(entidad_id)
        self.modos_entidad[entidad_id] = modo
        self._registrar_evento(
            "MODO_CONTABILIDAD_CAMBIADO", entidad_id, actor_id, momento,
            anterior.value if anterior else None, modo.value, motivo,
            (entidad_id,),
        )

    # ── Avocación, inhibición y visado ──────────────────────────────────

    def registrar_avocacion(
        self,
        evento_id: str,
        superior_id: str,
        inferior_id: str,
        competencia: str,
        alcance: str,
        momento: datetime,
        motivo: str,
    ) -> None:
        self._validar_fecha_evento(momento)
        if superior_id not in self.actores or inferior_id not in self.actores:
            raise ErrorDominio("Actor inexistente")
        superior = self.actores[superior_id]
        inferior = self.actores[inferior_id]
        if not superior.puede_ejecutar(inferior.rol):
            raise ErrorDominio("El superior no puede avocarse a competencia del inferior")
        self._registrar_evento(
            "AVOCACION_REGISTRADA", evento_id, superior_id, momento,
            None, {"inferior": inferior_id, "competencia": competencia, "alcance": alcance},
            motivo,
            (inferior_id,),
        )

    def registrar_inhibicion(
        self,
        evento_id: str,
        inferior_id: str,
        superior_id: str,
        competencia: str,
        alcance: str,
        momento: datetime,
        motivo: str,
    ) -> None:
        self._validar_fecha_evento(momento)
        if superior_id not in self.actores or inferior_id not in self.actores:
            raise ErrorDominio("Actor inexistente")
        superior = self.actores[superior_id]
        inferior = self.actores[inferior_id]
        if not superior.puede_ejecutar(inferior.rol):
            raise ErrorDominio("El superior no puede recibir inhibición del inferior")
        self._registrar_evento(
            "INHIBICION_REGISTRADA", evento_id, inferior_id, momento,
            None, {"superior": superior_id, "competencia": competencia, "alcance": alcance},
            motivo,
            (inferior_id,),
        )

    def registrar_visado(
        self,
        evento_id: str,
        visador_id: str,
        visado_id: str,
        tipo_visado: str,
        momento: datetime,
        motivo: str,
    ) -> None:
        self._validar_fecha_evento(momento)
        if visador_id not in self.actores:
            raise ErrorDominio("Visador inexistente")
        visador = self.actores[visador_id]
        if tipo_visado == "REGISTRO_NO_ASIENTO" and visador.rol != Rol.SUBDIRECTOR:
            raise ErrorDominio("Solo el SUBDIRECTOR puede visar registros contables no asientos")
        self._registrar_evento(
            "VISADO_REGISTRADO", evento_id, visador_id, momento,
            None, {"visado": visado_id, "tipo": tipo_visado},
            motivo,
            (visado_id,),
        )

    # ── Rol ADMIN ───────────────────────────────────────────────────────

    def solicitar_intervencion_admin(
        self,
        solicitud_id: str,
        solicitante_id: str,
        admin_id: str,
        solicitada_en: datetime,
        motivo: str,
    ) -> SolicitudAdmin:
        self._validar_fecha_evento(solicitada_en)
        if solicitante_id not in self.actores or admin_id not in self.actores:
            raise ErrorDominio("Actor inexistente")
        solicitante = self.actores[solicitante_id]
        admin = self.actores[admin_id]
        if solicitante.rol not in {Rol.JEFE_CONTABILIDAD, Rol.DIRECTOR}:
            raise ErrorDominio("Solo el JEFE DE CONTABILIDAD o el DIRECTOR pueden solicitar intervención del ADMIN")
        if admin.rol != Rol.ADMIN:
            raise ErrorDominio("El beneficiario debe ser un ADMIN")
        solicitud = SolicitudAdmin(
            solicitud_id=solicitud_id,
            solicitante_id=solicitante_id,
            admin_id=admin_id,
            solicitada_en=solicitada_en,
        )
        self.solicitudes_admin[solicitud_id] = solicitud
        self._registrar_evento(
            "SOLICITUD_ADMIN_REGISTRADA", solicitud_id, solicitante_id, solicitada_en,
            None, {"admin": admin_id, "motivo": motivo},
            "Solicitud de intervención ADMIN",
            (admin_id,),
        )
        return solicitud

    def presentar_informe_admin(
        self,
        informe_id: str,
        solicitud_id: str,
        redactado_por: str,
        presentado_en: datetime,
        repercusion_sustancia: str,
        graduacion_causa: str,
    ) -> InformeAdmin:
        self._validar_fecha_evento(presentado_en)
        solicitud = self.solicitudes_admin.get(solicitud_id)
        if solicitud is None:
            raise ErrorDominio("Solicitud de ADMIN inexistente")
        if redactado_por not in self.actores:
            raise ErrorDominio("Redactor inexistente")
        if self.actores[redactado_por].rol != Rol.JEFE_CONTABILIDAD:
            raise ErrorDominio("Solo el JEFE DE CONTABILIDAD puede redactar el informe de repercusión")
        informe = InformeAdmin(
            informe_id=informe_id,
            solicitud_id=solicitud_id,
            redactado_por=redactado_por,
            presentado_en=presentado_en,
            repercusion_sustancia=repercusion_sustancia,
            graduacion_causa=graduacion_causa,
        )
        self.informes_admin[informe_id] = informe
        solicitud.concluida_en = presentado_en
        solicitud.informe_id = informe_id
        self._registrar_evento(
            "INFORME_ADMIN_PRESENTADO", informe_id, redactado_por, presentado_en,
            None, {"solicitud": solicitud_id, "graduacion": graduacion_causa},
            "Informe de repercusión en sustancia contable",
            (solicitud_id,),
        )
        return informe

    def validar_informe_admin(
        self,
        informe_id: str,
        validador_id: str,
        validado: bool,
        momento: datetime,
        motivo: str,
    ) -> InformeAdmin:
        self._validar_fecha_evento(momento)
        informe = self.informes_admin.get(informe_id)
        if informe is None:
            raise ErrorDominio("Informe inexistente")
        if validador_id not in self.actores:
            raise ErrorDominio("Validador inexistente")
        validador = self.actores[validador_id]
        if validador.rol not in {Rol.JEFE_CONTABILIDAD, Rol.SUBDIRECTOR, Rol.DIRECTOR}:
            raise ErrorDominio("El validador debe ser JEFE DE CONTABILIDAD, SUBDIRECTOR o DIRECTOR")
        informe.validado = validado
        self._registrar_evento(
            "INFORME_ADMIN_VALIDADO", informe_id, validador_id, momento,
            None, {"solicitud": informe.solicitud_id, "validado": validado},
            motivo,
            (informe.solicitud_id,),
        )
        return informe

    # ── Remisión a investigación ────────────────────────────────────────

    def registrar_remision_investigacion(
        self,
        remision_id: str,
        hecho_economico_id: str,
        promovido_por: str,
        promovida_en: datetime,
        motivo: str,
    ) -> RemisionInvestigacion:
        self._validar_fecha_evento(promovida_en)
        if promovido_por not in self.actores:
            raise ErrorDominio("Promotor inexistente")
        promotor = self.actores[promovido_por]
        if promotor.rol not in {Rol.JEFE_CONTABILIDAD, Rol.SUBDIRECTOR, Rol.DIRECTOR}:
            raise ErrorDominio("Solo JEFE DE CONTABILIDAD, SUBDIRECTOR o DIRECTOR pueden promover remisión")
        if hecho_economico_id not in self.hechos:
            raise ErrorDominio("Hecho económico inexistente")
        remision = RemisionInvestigacion(
            remision_id=remision_id,
            hecho_economico_id=hecho_economico_id,
            promovido_por=promovido_por,
            promovida_en=promovida_en,
        )
        self.remisiones[remision_id] = remision
        self._registrar_evento(
            "REMISION_INVESTIGACION_INICIADA", remision_id, promovido_por, promovida_en,
            None, {"hecho": hecho_economico_id},
            motivo,
            (hecho_economico_id,),
        )
        return remision

    def finalizar_remision_investigacion(
        self,
        remision_id: str,
        informe_id: str,
        finalizada_en: datetime,
        motivo: str,
    ) -> RemisionInvestigacion:
        self._validar_fecha_evento(finalizada_en)
        remision = self.remisiones.get(remision_id)
        if remision is None:
            raise ErrorDominio("Remisión inexistente")
        if remision.finalizada_en is not None:
            raise ErrorDominio("La remisión ya está finalizada")
        if informe_id not in self.informes_admin:
            raise ErrorDominio("Informe de investigación inexistente")
        remision.finalizada_en = finalizada_en
        remision.informe_id = informe_id
        self._registrar_evento(
            "REMISION_INVESTIGACION_FINALIZADA", remision_id, remision.promovido_por, finalizada_en,
            None, {"informe": informe_id},
            motivo,
            (remision.hecho_economico_id,),
        )
        return remision

    # ── Condición de alteración por monto ───────────────────────────────

    def registrar_alerta_importe(
        self,
        alerta_id: str,
        grupo: str,
        subgrupo: str,
        sub_subgrupo: str | None,
        monto_umbral: int,
        criticidad: CriticidadImporte,
        notificar_a: str,
    ) -> AlertaImporte:
        alerta = AlertaImporte(
            grupo=grupo,
            subgrupo=subgrupo,
            sub_subgrupo=sub_subgrupo,
            monto_umbral=monto_umbral,
            criticidad=criticidad,
            notificar_a=notificar_a,
        )
        self.alertas_importe[alerta_id] = alerta
        return alerta

    def evaluar_criticidad_importe(
        self,
        importe_quebranto: int,
        beneficio_industrial_anterior: int,
    ) -> tuple[CriticidadImporte, str | None]:
        if beneficio_industrial_anterior <= 0:
            raise ErrorDominio("El beneficio industrial anterior debe ser positivo")
        porcentaje = round(importe_quebranto / beneficio_industrial_anterior, 10)
        umbral_critico = round(0.20, 10)
        umbral_2_3 = round((2 / 3) * umbral_critico, 10)
        umbral_0_5 = round(0.5 * umbral_critico, 10)
        umbral_0_4 = round(0.4 * umbral_critico, 10)
        umbral_0_3 = round(0.3 * umbral_critico, 10)
        umbral_0_2 = round(0.2 * umbral_critico, 10)
        if porcentaje >= umbral_critico:
            return CriticidadImporte.CRITICA, "DIRECTOR"
        if umbral_2_3 <= porcentaje < umbral_critico:
            return CriticidadImporte.CUASI_CRITICA, "SUBDIRECTOR"
        if umbral_0_5 <= porcentaje < umbral_2_3:
            return CriticidadImporte.MEDIA, None
        if umbral_0_4 <= porcentaje < umbral_0_5:
            return CriticidadImporte.BAJA_INFORMATIVA, "DIRECTOR"
        if umbral_0_3 <= porcentaje < umbral_0_4:
            return CriticidadImporte.BAJA_INFORMATIVA, "SUBDIRECTOR"
        if umbral_0_2 <= porcentaje < umbral_0_3:
            return CriticidadImporte.BAJA_INFORMATIVA, "JEFE_CONTABILIDAD"
        return CriticidadImporte.BAJA_INFORMATIVA, None

    # ── Registro contable no asiento ────────────────────────────────────

    def registrar_registro_no_asiento(
        self,
        registro_id: str,
        tipo_registro: str,
        ejecutado_por: str,
        visado_por: str | None,
        causa: str,
        registrado_en: datetime,
    ) -> RegistroNoAsiento:
        self._validar_fecha_evento(registrado_en)
        if ejecutado_por not in self.actores:
            raise ErrorDominio("Ejecutor inexistente")
        if self.actores[ejecutado_por].rol != Rol.JEFE_CONTABILIDAD:
            raise ErrorDominio("Solo el JEFE DE CONTABILIDAD puede ejecutar registros contables no asientos")
        if visado_por is not None:
            if visado_por not in self.actores:
                raise ErrorDominio("Visador inexistente")
            if self.actores[visado_por].rol != Rol.SUBDIRECTOR:
                raise ErrorDominio("Solo el SUBDIRECTOR puede visar registros contables no asientos")
        registro = RegistroNoAsiento(
            registro_id=registro_id,
            tipo_registro=tipo_registro,
            ejecutado_por=ejecutado_por,
            visado_por=visado_por,
            visado_en=registrado_en if visado_por else None,
            causa=causa,
            registrado_en=registrado_en,
        )
        self.registros_no_asiento[registro_id] = registro
        self._registrar_evento(
            "REGISTRO_NO_ASIENTO_REGISTRADO", registro_id, ejecutado_por, registrado_en,
            None, {"tipo": tipo_registro, "causa": causa, "visado": visado_por},
            "Registro contable no asiento",
        )
        return registro

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
                "estado_anterior": _normalizar_json(evento.estado_anterior),
                "estado_posterior": _normalizar_json(evento.estado_posterior),
                "payload": _normalizar_json(evento.payload),
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
        eventos = [evento for evento in self.eventos if evento.timestamp <= fecha_epistemica]
        entidades: dict[str, Any] = {}
        actores: dict[str, Any] = {}
        fuentes: dict[str, Any] = {}
        hechos: dict[str, dict[str, Any]] = {}
        evidencias: dict[str, dict[str, Any]] = {}
        valoraciones_evidencia: dict[str, Any] = {}
        criterios: dict[str, Any] = {}
        autorizaciones: dict[str, Any] = {}
        interpretaciones: dict[str, dict[str, Any]] = {}
        decisiones: dict[str, dict[str, Any]] = {}
        representaciones: dict[str, dict[str, Any]] = {}
        rectificaciones: dict[str, Any] = {}
        permisos: dict[str, Any] = {}
        modos_entidad: dict[str, str] = {}
        avocaciones: dict[str, Any] = {}
        inhibiciones: dict[str, Any] = {}
        visados: dict[str, Any] = {}
        solicitudes_admin: dict[str, Any] = {}
        informes_admin: dict[str, Any] = {}
        remisiones: dict[str, Any] = {}
        registros_no_asiento: dict[str, Any] = {}

        for evento in eventos:
            snapshot = _normalizar_json(evento.estado_posterior)
            if evento.tipo == "ENTIDAD_REGISTRADA":
                entidades[evento.objeto_id] = snapshot
            elif evento.tipo == "ACTOR_REGISTRADO":
                actores[evento.objeto_id] = snapshot
            elif evento.tipo == "FUENTE_REGISTRADA":
                fuentes[evento.objeto_id] = snapshot
            if evento.tipo == "HECHO_REGISTRADO":
                snapshot = evento.payload.get("hecho", {})
                hechos[evento.objeto_id] = {
                    **snapshot,
                    "hecho_id": evento.objeto_id,
                    "tipo": snapshot.get("tipo", evento.payload.get("tipo")),
                    "estado_epistemologico": _normalizar_json(evento.estado_posterior),
                }
            elif evento.tipo == "ESTADO_EPISTEMICO_CAMBIADO" and evento.objeto_id in hechos:
                hechos[evento.objeto_id]["estado_epistemologico"] = _normalizar_json(evento.estado_posterior)
            elif evento.tipo == "HECHO_RELACIONADO" and evento.objeto_id in hechos:
                hechos[evento.objeto_id]["relaciones"] = snapshot
            elif evento.tipo == "EVIDENCIA_RECIBIDA":
                evidencias[evento.objeto_id] = snapshot
            elif evento.tipo == "EVIDENCIA_ASOCIADA":
                valoracion_id = f"{snapshot.get('hecho_id')}:{snapshot.get('evidencia_id')}"
                valoraciones_evidencia[valoracion_id] = snapshot
            elif evento.tipo == "CRITERIO_REGISTRADO":
                criterios[evento.objeto_id] = snapshot
            elif evento.tipo == "AUTORIZACION_OTORGADA":
                autorizaciones[evento.objeto_id] = snapshot
            elif evento.tipo == "AUTORIZACION_REVOCADA":
                autorizaciones[evento.objeto_id] = snapshot
            elif evento.tipo == "PERMISO_CONCEDIDO":
                permisos[evento.objeto_id] = snapshot
            elif evento.tipo == "PERMISO_REVOCADO":
                permiso = permisos.setdefault(evento.objeto_id, {})
                permiso.update(snapshot)
                permiso["revocada_por"] = evento.actor_id
                permiso["motivo_revocacion"] = evento.motivo
            elif evento.tipo == "MODO_CONTABILIDAD_CAMBIADO":
                modos_entidad[evento.objeto_id] = evento.estado_posterior
            elif evento.tipo == "AVOCACION_REGISTRADA":
                avocaciones[evento.objeto_id] = {"superior": evento.actor_id, **snapshot}
            elif evento.tipo == "INHIBICION_REGISTRADA":
                inhibiciones[evento.objeto_id] = {"inferior": evento.actor_id, **snapshot}
            elif evento.tipo == "VISADO_REGISTRADO":
                visados[evento.objeto_id] = {"visador": evento.actor_id, **snapshot}
            elif evento.tipo == "SOLICITUD_ADMIN_REGISTRADA":
                solicitudes_admin[evento.objeto_id] = {"solicitante": evento.actor_id, **snapshot}
            elif evento.tipo == "INFORME_ADMIN_PRESENTADO":
                informes_admin[evento.objeto_id] = {"redactado_por": evento.actor_id, **snapshot}
            elif evento.tipo == "INFORME_ADMIN_VALIDADO":
                informe = informes_admin.setdefault(evento.objeto_id, {})
                informe.update(snapshot)
                informe["validado_por"] = evento.actor_id
            elif evento.tipo == "REMISION_INVESTIGACION_INICIADA":
                remisiones[evento.objeto_id] = {"promovido_por": evento.actor_id, **snapshot}
            elif evento.tipo == "REMISION_INVESTIGACION_FINALIZADA":
                remision = remisiones.setdefault(evento.objeto_id, {})
                remision["finalizada_en"] = evento.timestamp.isoformat()
                remision["informe"] = snapshot.get("informe")
            elif evento.tipo == "REGISTRO_NO_ASIENTO_REGISTRADO":
                registros_no_asiento[evento.objeto_id] = {"ejecutado_por": evento.actor_id, **snapshot}
            elif evento.tipo == "INTERPRETACION_PROPUESTA":
                interpretaciones[evento.objeto_id] = snapshot
            elif evento.tipo == "DECISION_ADOPTADA":
                interpretacion_id = snapshot.get("interpretacion_adoptada_id")
                decisiones[evento.objeto_id] = {
                    **snapshot,
                    "interpretacion": interpretacion_id,
                }
                for estado_id, estado in evento.payload.get("interpretaciones_estado", {}).items():
                    if estado_id in interpretaciones:
                        interpretaciones[estado_id]["estado"] = estado
            elif evento.tipo == "REPRESENTACION_REGISTRADA":
                lineas = snapshot.get("lineas", [])
                representaciones[evento.objeto_id] = {
                    **snapshot,
                    "decision": snapshot.get("decision_id"),
                    "cuadra": sum(l.get("debe", 0) for l in lineas) == sum(
                        l.get("haber", 0) for l in lineas
                    ),
                    "fecha_contable": snapshot.get("fecha_contable"),
                    "registrada_en": snapshot.get("registrada_en"),
                }
            elif evento.tipo == "RECTIFICACION_REGISTRADA":
                rectificaciones[evento.objeto_id] = snapshot
                for representacion_id, estado in evento.payload.get(
                    "estados_representaciones", {}
                ).items():
                    if representacion_id in representaciones:
                        representaciones[representacion_id]["estado"] = estado
        ejercicios: dict[str, dict[str, Any]] = {}
        for evento in eventos:
            if evento.tipo == "EJERCICIO_REGISTRADO":
                ejercicios[evento.objeto_id] = {
                    "entidad_id": evento.payload["entidad_id"],
                    "inicio": evento.payload["inicio"],
                    "fin": evento.payload["fin"],
                    "estado": "ABIERTO",
                    "eventos_estado": [],
                }
            elif evento.tipo in {"EJERCICIO_CERRADO", "EJERCICIO_REABIERTO"}:
                estado = ejercicios.get(evento.objeto_id)
                if estado is not None:
                    estado["estado"] = evento.estado_posterior
                    estado["eventos_estado"].append({
                        "tipo": evento.tipo,
                        "timestamp": evento.timestamp.isoformat(),
                        "actor_id": evento.actor_id,
                        "motivo": evento.motivo,
                        "referencias": list(evento.referencia_ids),
                    })
        cierres = [
            {
                "cierre_id": evento.payload["cierre_id"],
                "ejercicio_id": evento.objeto_id,
                "fecha_cierre": evento.payload["fecha_cierre"],
                "registrado_en": evento.timestamp.isoformat(),
                "resultado_ejercicio": evento.payload["resultado_ejercicio"],
                "representacion_ids": evento.payload.get("representacion_ids", []),
                "autorizacion_id": evento.payload.get("autorizacion_id"),
                "actor_id": evento.actor_id,
                "motivo": evento.motivo,
                "regularizacion": evento.payload["regularizacion"],
                "asiento_cierre": evento.payload["asiento_cierre"],
                "asiento_apertura": evento.payload["asiento_apertura"],
            }
            for evento in eventos
            if evento.tipo == "EJERCICIO_CERRADO"
        ]
        return {
            "entidades": entidades,
            "actores": actores,
            "fuentes": fuentes,
            "fecha_epistemica": fecha_epistemica.isoformat(),
            "hechos": list(hechos.values()),
            "evidencias": evidencias,
            "valoraciones_evidencia": valoraciones_evidencia,
            "criterios": criterios,
            "autorizaciones": autorizaciones,
            "interpretaciones": interpretaciones,
            "decisiones": decisiones,
            "representaciones": representaciones,
            "rectificaciones": rectificaciones,
            "permisos": permisos,
            "modos_entidad": modos_entidad,
            "avocaciones": avocaciones,
            "inhibiciones": inhibiciones,
            "visados": visados,
            "solicitudes_admin": solicitudes_admin,
            "informes_admin": informes_admin,
            "remisiones": remisiones,
            "registros_no_asiento": registros_no_asiento,
            "ejercicios": ejercicios,
            "cierres": cierres,
            "eventos_disponibles": len(eventos),
        }
