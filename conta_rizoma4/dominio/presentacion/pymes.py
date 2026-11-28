"""Paquete analítico de estados PGC-PYMES, sin pretensión de depósito oficial."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Optional

from .presentacion import ReglaPresentacion, REGLAS_PGC_ANALITICAS, presentar_pgc


@dataclass(frozen=True)
class PresentacionPymes:
    empresa_id: str
    ejercicio: str
    ejercicio_comparativo: Optional[str]
    balance: dict
    cuenta_pyg: dict
    balance_comparativo: Optional[dict]
    pyg_comparativa: Optional[dict]
    estado_cambios_patrimonio_neto: Optional[dict]
    datos_memoria: Optional[dict]
    documentos_integrantes: tuple[str, ...]
    pendientes: tuple[str, ...]
    trazabilidad_reglas: tuple[dict, ...] = ()
    perfil_presentacion: str = "PGC_PYMES_ANALITICO_V1"
    apta_para_deposito: bool = False


def presentar_pymes(
    mayor: dict,
    *,
    empresa_id: str,
    ejercicio: str,
    mayor_comparativo: Optional[dict] = None,
    ejercicio_comparativo: Optional[str] = None,
    datos_memoria: Optional[dict] = None,
    datos_ecpn: Optional[dict] = None,
    reglas: tuple[ReglaPresentacion, ...] = REGLAS_PGC_ANALITICAS,
) -> PresentacionPymes:
    """Prepara una vista PGC-PYMES y declara lo que falta para formularla.

    ``mayor`` y ``mayor_comparativo`` son balances de comprobación por cuenta
    de cada ejercicio. ``datos_memoria`` contiene únicamente información
    explícitamente suministrada; este caso de uso no inventa políticas,
    hechos, autorizaciones ni aplicación de resultados.
    """
    if not empresa_id.strip() or not ejercicio.strip():
        raise ValueError("empresa_id y ejercicio son obligatorios")
    if mayor_comparativo is not None and not ejercicio_comparativo:
        raise ValueError("Debe identificarse el ejercicio comparativo aportado")
    if ejercicio_comparativo == ejercicio:
        raise ValueError("El ejercicio comparativo debe ser distinto del ejercicio actual")
    if datos_memoria is not None and not isinstance(datos_memoria, dict):
        raise ValueError("datos_memoria debe ser un diccionario o None")
    if datos_ecpn is not None and not isinstance(datos_ecpn, dict):
        raise ValueError("datos_ecpn debe ser un diccionario o None")
    ecpn = _validar_ecpn(datos_ecpn) if datos_ecpn is not None else None

    version = "PGC_PYMES_ANALITICO_V1"
    balance = presentar_pgc(mayor, version, reglas)
    pyg = balance
    comparativo = presentar_pgc(mayor_comparativo, version, reglas) if mayor_comparativo is not None else None

    pendientes: list[str] = []
    if comparativo is None:
        pendientes.append("No se aportó el mayor del ejercicio comparativo")
    if not datos_memoria:
        pendientes.append("No se aportaron datos de memoria")
    if not ecpn:
        pendientes.append("No se aportaron datos del estado de cambios en el patrimonio neto")
    else:
        if not ecpn["cuadra"]:
            pendientes.append("El estado de cambios en el patrimonio neto no concilia")
        pendientes.append("La suficiencia y clasificación de los movimientos del ECPN requieren revisión")
    pendientes.append("Contenido y suficiencia de la memoria requieren revisión")
    if balance.cuentas_sin_clasificar:
        pendientes.append("Hay saldos del ejercicio actual sin regla de presentación")
    if balance.cuadre is not True:
        pendientes.append("El balance actual no supera el control aritmético")
    if comparativo and comparativo.cuentas_sin_clasificar:
        pendientes.append("Hay saldos comparativos sin regla de presentación")
    if comparativo and comparativo.cuadre is not True:
        pendientes.append("El balance comparativo no supera el control aritmético")

    reglas_aplicadas = balance.reglas_aplicadas
    trazabilidad = tuple({
        "prefijo": regla.prefijo,
        "seccion": regla.seccion,
        "epigrafe": regla.epigrafe,
        "factor": regla.factor,
        "fuente": regla.fuente,
        "referencia_normativa": regla.referencia_normativa,
        "vigente_desde": regla.vigente_desde.isoformat() if regla.vigente_desde else None,
        "vigente_hasta": regla.vigente_hasta.isoformat() if regla.vigente_hasta else None,
        "revisada_por": regla.revisada_por,
        "revisada_en": regla.revisada_en.isoformat() if regla.revisada_en else None,
        "cuentas_afectadas": tuple(sorted(
            cuenta for cuenta in mayor
            if max((r for r in reglas if cuenta.startswith(r.prefijo)),
                   key=lambda r: len(r.prefijo), default=None) == regla
        )),
    } for regla in reglas_aplicadas)
    if any(regla.referencia_normativa is None or regla.revisada_por is None
           for regla in reglas_aplicadas):
        pendientes.append("Las reglas aplicadas carecen de referencia normativa o revisión competente")

    return PresentacionPymes(
        empresa_id=empresa_id,
        ejercicio=ejercicio,
        ejercicio_comparativo=ejercicio_comparativo,
        balance=balance.balance_situacion,
        cuenta_pyg=balance.cuenta_pyg,
        balance_comparativo=comparativo.balance_situacion if comparativo else None,
        pyg_comparativa=comparativo.cuenta_pyg if comparativo else None,
        estado_cambios_patrimonio_neto=ecpn,
        datos_memoria=deepcopy(datos_memoria) if datos_memoria is not None else None,
        documentos_integrantes=("balance", "cuenta_pyg", "ecpn", "memoria"),
        pendientes=tuple(pendientes),
        trazabilidad_reglas=trazabilidad,
    )


def _validar_ecpn(datos: dict) -> dict:
    """Calcula la conciliación aritmética a partir de variaciones expresas.

    No infiere movimientos ni comprueba por sí solo que la clasificación sea
    completa conforme al modelo oficial.
    """
    requerido = {"saldo_inicial_centimos", "variaciones", "saldo_final_centimos"}
    if set(datos) != requerido:
        raise ValueError("datos_ecpn debe contener saldo_inicial_centimos, variaciones y saldo_final_centimos")
    inicial = datos["saldo_inicial_centimos"]
    final = datos["saldo_final_centimos"]
    variaciones = datos["variaciones"]
    if type(inicial) is not int or type(final) is not int:
        raise ValueError("Los saldos inicial y final del ECPN deben ser céntimos enteros")
    if not isinstance(variaciones, list):
        raise ValueError("variaciones del ECPN debe ser una lista explícita")
    sumatoria = 0
    copia_variaciones = []
    for variacion in variaciones:
        if not isinstance(variacion, dict) or set(variacion) != {"concepto", "importe_centimos"}:
            raise ValueError("Cada variación ECPN requiere concepto e importe_centimos")
        concepto = variacion["concepto"]
        importe = variacion["importe_centimos"]
        if not isinstance(concepto, str) or not concepto.strip() or type(importe) is not int:
            raise ValueError("Concepto ECPN obligatorio e importe expresado como céntimos enteros")
        sumatoria += importe
        copia_variaciones.append({"concepto": concepto, "importe_centimos": importe})
    diferencia = inicial + sumatoria - final
    return {
        "saldo_inicial_centimos": inicial,
        "variaciones": copia_variaciones,
        "total_variaciones_centimos": sumatoria,
        "saldo_final_centimos": final,
        "diferencia_conciliacion_centimos": diferencia,
        "cuadra": diferencia == 0,
    }
