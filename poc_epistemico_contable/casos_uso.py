"""Casos de uso del primer núcleo, independientes de infraestructura."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from .modelo import (
    Actor,
    Autorizacion,
    Criterio,
    Decision,
    Evidencia,
    HechoEconomico,
    Interpretacion,
    RepresentacionContable,
)
from .nucleo import NucleoEpistemicoContable


class RegistrarHecho:
    def __init__(self, nucleo: NucleoEpistemicoContable) -> None:
        self.nucleo = nucleo

    def ejecutar(self, hecho: HechoEconomico, actor_id: str) -> HechoEconomico:
        return self.nucleo.registrar_hecho(hecho, actor_id)


class IncorporarEvidencia:
    def __init__(self, nucleo: NucleoEpistemicoContable) -> None:
        self.nucleo = nucleo

    def ejecutar(self, evidencia: Evidencia, actor_id: str) -> Evidencia:
        return self.nucleo.registrar_evidencia(evidencia, actor_id)


class ProponerInterpretacion:
    def __init__(self, nucleo: NucleoEpistemicoContable) -> None:
        self.nucleo = nucleo

    def ejecutar(self, interpretacion: Interpretacion, actor_id: str) -> Interpretacion:
        return self.nucleo.proponer_interpretacion(interpretacion, actor_id)


class RegistrarCriterio:
    def __init__(self, nucleo: NucleoEpistemicoContable) -> None:
        self.nucleo = nucleo

    def ejecutar(self, criterio: Criterio, actor_id: str) -> Criterio:
        return self.nucleo.registrar_criterio(criterio, actor_id)


class AdoptarDecision:
    def __init__(self, nucleo: NucleoEpistemicoContable) -> None:
        self.nucleo = nucleo

    def ejecutar(self, decision: Decision) -> Decision:
        return self.nucleo.adoptar_decision(decision)


class RegistrarRepresentacion:
    def __init__(self, nucleo: NucleoEpistemicoContable) -> None:
        self.nucleo = nucleo

    def ejecutar(self, representacion: RepresentacionContable,
                 actor_id: str) -> RepresentacionContable:
        return self.nucleo.crear_representacion(representacion, actor_id)


class ReconstruirEstado:
    def __init__(self, nucleo: NucleoEpistemicoContable) -> None:
        self.nucleo = nucleo

    def ejecutar(self, fecha_epistemica: datetime) -> dict:
        return self.nucleo.reconstruir(fecha_epistemica)
