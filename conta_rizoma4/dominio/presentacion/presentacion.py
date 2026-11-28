"""Transformaciones normales de balance, PyG y declaración fiscal."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


SECCIONES_PGC = frozenset({
    "activo", "pasivo", "patrimonio_neto", "gasto", "ingreso",
})


@dataclass(frozen=True)
class ReglaPresentacion:
    """Regla explícita de presentación por prefijo de cuenta.

    ``factor`` normaliza el saldo del mayor para mostrarlo con el signo de la
    partida: +1 para partidas deudoras, -1 para partidas acreedoras. Los
    correctores de activo conservan factor +1 y se presentan negativos.
    """

    prefijo: str
    seccion: str
    epigrafe: str
    factor: int
    fuente: str = "Regla analítica interna; pendiente de validación normativa"
    referencia_normativa: str | None = None
    vigente_desde: date | None = None
    vigente_hasta: date | None = None
    revisada_por: str | None = None
    revisada_en: date | None = None

    def __post_init__(self) -> None:
        if not self.prefijo or not self.epigrafe:
            raise ValueError("La regla requiere prefijo y epígrafe")
        if self.seccion not in SECCIONES_PGC:
            raise ValueError(f"Sección no admitida: {self.seccion}")
        if self.factor not in (-1, 1):
            raise ValueError("factor debe ser -1 o 1")
        if self.vigente_desde and self.vigente_hasta and self.vigente_hasta < self.vigente_desde:
            raise ValueError("La vigencia de la regla termina antes de comenzar")
        if (self.revisada_por is None) != (self.revisada_en is None):
            raise ValueError("La revisión requiere identidad y fecha")


@dataclass(frozen=True)
class PresentacionPGC:
    balance_situacion: dict
    cuenta_pyg: dict
    version_normativa: str
    reglas_aplicadas: tuple[ReglaPresentacion, ...] = ()
    cuentas_sin_clasificar: dict[str, int] = field(default_factory=dict)
    cuadre: Optional[bool] = None


@dataclass(frozen=True)
class PresentacionAEAT:
    modelo: str
    periodo: str
    datos: dict
    version_normativa: str


REGLAS_PGC_ANALITICAS: tuple[ReglaPresentacion, ...] = (
    ReglaPresentacion("28", "activo", "inmovilizado_no_corriente", 1),
    ReglaPresentacion("29", "activo", "inmovilizado_no_corriente", 1),
    ReglaPresentacion("20", "activo", "inmovilizado_no_corriente", 1),
    ReglaPresentacion("21", "activo", "inmovilizado_no_corriente", 1),
    ReglaPresentacion("22", "activo", "inmovilizado_no_corriente", 1),
    ReglaPresentacion("23", "activo", "inmovilizado_no_corriente", 1),
    ReglaPresentacion("24", "activo", "inmovilizado_no_corriente", 1),
    ReglaPresentacion("25", "activo", "inmovilizado_no_corriente", 1),
    ReglaPresentacion("26", "activo", "inmovilizado_no_corriente", 1),
    ReglaPresentacion("27", "activo", "inmovilizado_no_corriente", 1),
    ReglaPresentacion("30", "activo", "existencias", 1),
    ReglaPresentacion("31", "activo", "existencias", 1),
    ReglaPresentacion("32", "activo", "existencias", 1),
    ReglaPresentacion("33", "activo", "existencias", 1),
    ReglaPresentacion("34", "activo", "existencias", 1),
    ReglaPresentacion("35", "activo", "existencias", 1),
    ReglaPresentacion("36", "activo", "existencias", 1),
    ReglaPresentacion("39", "activo", "existencias", 1),
    ReglaPresentacion("40", "pasivo", "acreedores_comerciales", -1),
    ReglaPresentacion("407", "activo", "anticipos_a_proveedores", 1),
    ReglaPresentacion("41", "pasivo", "acreedores_comerciales", -1),
    ReglaPresentacion("43", "activo", "deudores_comerciales", 1),
    ReglaPresentacion("438", "pasivo", "anticipos_de_clientes", -1),
    ReglaPresentacion("44", "activo", "deudores_comerciales", 1),
    ReglaPresentacion("460", "activo", "deudores_comerciales", 1),
    ReglaPresentacion("465", "pasivo", "acreedores_comerciales", -1),
    ReglaPresentacion("470", "activo", "activos_fiscales", 1),
    ReglaPresentacion("472", "activo", "activos_fiscales", 1),
    ReglaPresentacion("475", "pasivo", "pasivos_fiscales", -1),
    ReglaPresentacion("476", "pasivo", "pasivos_fiscales", -1),
    ReglaPresentacion("477", "pasivo", "pasivos_fiscales", -1),
    ReglaPresentacion("480", "activo", "periodificaciones", 1),
    ReglaPresentacion("485", "pasivo", "periodificaciones", -1),
    ReglaPresentacion("49", "activo", "deudores_comerciales", 1),
    ReglaPresentacion("10", "patrimonio_neto", "capital", -1),
    ReglaPresentacion("11", "patrimonio_neto", "reservas", -1),
    ReglaPresentacion("12", "patrimonio_neto", "resultados_acumulados", -1),
    ReglaPresentacion("13", "patrimonio_neto", "subvenciones_y_ajustes_pn", -1),
    ReglaPresentacion("14", "pasivo", "provisiones_largo_plazo", -1),
    ReglaPresentacion("15", "pasivo", "deudas_largo_plazo", -1),
    ReglaPresentacion("16", "pasivo", "deudas_largo_plazo", -1),
    ReglaPresentacion("17", "pasivo", "deudas_largo_plazo", -1),
    ReglaPresentacion("18", "pasivo", "pasivos_largo_plazo", -1),
    ReglaPresentacion("50", "pasivo", "deudas_corto_plazo", -1),
    ReglaPresentacion("51", "pasivo", "deudas_corto_plazo", -1),
    ReglaPresentacion("52", "pasivo", "deudas_corto_plazo", -1),
    ReglaPresentacion("53", "activo", "inversiones_corto_plazo", 1),
    ReglaPresentacion("54", "activo", "inversiones_corto_plazo", 1),
    ReglaPresentacion("57", "activo", "efectivo", 1),
    ReglaPresentacion("58", "activo", "activos_mantenidos_venta", 1),
    ReglaPresentacion("59", "activo", "inversiones_corto_plazo", 1),
    ReglaPresentacion("6", "gasto", "gastos_explotacion_y_financieros", 1),
    ReglaPresentacion("7", "ingreso", "ingresos_explotacion_y_financieros", -1),
)


def presentar_pgc(
    mayor: dict,
    version_normativa: str = "PGC_ES_ANALITICO_V1",
    reglas: tuple[ReglaPresentacion, ...] = REGLAS_PGC_ANALITICAS,
) -> PresentacionPGC:
    """Genera una vista derivada; no afirma que sea un modelo de depósito.

    Usa la regla de prefijo más largo. Los saldos sin regla se devuelven
    explícitamente y hacen que ``cuadre`` sea ``None``: no se declara un
    balance validado mientras haya importes sin clasificar.
    """
    prefijos = [r.prefijo for r in reglas]
    if len(prefijos) != len(set(prefijos)):
        raise ValueError("Hay prefijos duplicados en las reglas de presentación")

    secciones: dict[str, dict[str, dict[str, int]]] = {
        seccion: {} for seccion in SECCIONES_PGC
    }
    sin_clasificar: dict[str, int] = {}
    reglas_encontradas: set[ReglaPresentacion] = set()
    reglas_ordenadas = sorted(reglas, key=lambda x: len(x.prefijo), reverse=True)
    for cuenta, datos in mayor.items():
        saldo = datos.get("saldo")
        if type(saldo) is not int:
            raise ValueError(f"Saldo no entero para la cuenta {cuenta!r}")
        regla = next((r for r in reglas_ordenadas if cuenta.startswith(r.prefijo)), None)
        if regla is None:
            if saldo:
                sin_clasificar[cuenta] = saldo
            continue
        importe = saldo * regla.factor
        epigrafe = secciones[regla.seccion].setdefault(regla.epigrafe, {})
        epigrafe[cuenta] = importe
        reglas_encontradas.add(regla)

    activo = secciones["activo"]
    pasivo = secciones["pasivo"]
    patrimonio = secciones["patrimonio_neto"]
    gastos = secciones["gasto"]
    ingresos = secciones["ingreso"]
    total_activo = sum(sum(cuentas.values()) for cuentas in activo.values())
    total_pasivo = sum(sum(cuentas.values()) for cuentas in pasivo.values())
    total_patrimonio = sum(sum(cuentas.values()) for cuentas in patrimonio.values())
    total_gastos = sum(sum(cuentas.values()) for cuentas in gastos.values())
    total_ingresos = sum(sum(cuentas.values()) for cuentas in ingresos.values())
    resultado = total_ingresos - total_gastos
    cuadre = None if sin_clasificar else total_activo == total_pasivo + total_patrimonio + resultado
    def aplanar(grupos: dict[str, dict[str, int]]) -> dict[str, int]:
        return {cuenta: importe for cuentas in grupos.values() for cuenta, importe in cuentas.items()}
    balance = {
        "activo": aplanar(activo),
        "activo_por_epigrafe": activo,
        "pasivo": aplanar(pasivo),
        "pasivo_por_epigrafe": pasivo,
        "patrimonio_neto": aplanar(patrimonio),
        "patrimonio_neto_por_epigrafe": patrimonio,
        "cuentas_sin_clasificar": dict(sin_clasificar),
        "total_activo": total_activo,
        "total_pasivo": total_pasivo,
        "total_patrimonio_neto": total_patrimonio,
        "resultado_ejercicio": resultado,
        "cuadra": cuadre,
    }
    pyg = {
        "gastos": aplanar(gastos),
        "gastos_por_epigrafe": gastos,
        "ingresos": aplanar(ingresos),
        "ingresos_por_epigrafe": ingresos,
        "total_gastos": total_gastos,
        "total_ingresos": total_ingresos,
        "resultado": resultado,
        "cuentas_sin_clasificar": dict(sin_clasificar),
    }
    reglas_usadas = tuple(r for r in reglas if r in reglas_encontradas)
    return PresentacionPGC(balance, pyg, version_normativa, reglas_usadas, sin_clasificar, cuadre)


def presentar_303(modelo, periodo: str, version_normativa: str = "AEAT_303") -> PresentacionAEAT:
    return PresentacionAEAT(
        modelo="303",
        periodo=periodo,
        datos={
            "iva_repercutido": modelo.iva_repercutido,
            "iva_soportado": modelo.iva_soportado,
            "diferencia": modelo.diferencia,
            "resultado": modelo.resultado,
        },
        version_normativa=version_normativa,
    )
