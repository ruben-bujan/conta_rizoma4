# -*- coding: utf-8 -*-
"""Pruebas unitarias del control administrativo empresa ↔ caso RIZOMA4."""
from __future__ import annotations

import pytest

from conta_rizoma4.api.routers import empresas
from conta_rizoma4.custodia.casos_rizoma4 import CasoRizoma4Error, validar_caso_id


class RepoFalso:
    datos = {}

    def listar(self, empresa_id, solo_activos=True):
        return [v for (e, _), v in self.datos.items() if e == empresa_id and (v["activo"] or not solo_activos)]

    def asociar(self, empresa_id, caso_id, actor):
        row = {"empresa_id": empresa_id, "caso_id": caso_id, "activo": True, "creado_por": actor}
        self.datos[(empresa_id, caso_id)] = row
        return row

    def desasociar(self, empresa_id, caso_id, actor):
        row = self.datos.get((empresa_id, caso_id))
        if not row or not row["activo"]:
            return None
        row = dict(row, activo=False)
        self.datos[(empresa_id, caso_id)] = row
        return row

    def esta_asociado(self, empresa_id, caso_id):
        row = self.datos.get((empresa_id, caso_id))
        return bool(row and row["activo"])


class ClienteFalso:
    def listar_casos(self):
        return [{"caso_id": "CASO_A", "nombre": "Caso A"}, {"caso_id": "CASO_B", "nombre": "Caso B"}]


@pytest.fixture(autouse=True)
def limpiar_falsos(monkeypatch):
    RepoFalso.datos = {}
    monkeypatch.setattr(empresas, "RepositorioCasoRizoma4", RepoFalso)
    monkeypatch.setattr(empresas, "ClienteRizoma4", ClienteFalso)


def test_validar_caso_id_acepta_formato_rizoma4():
    assert validar_caso_id("CASO_01-a") == "CASO_01-a"


@pytest.mark.parametrize("valor", ["", "caso con espacios", "a/b", "ámbito"])
def test_validar_caso_id_rechaza_formato_invalido(valor):
    with pytest.raises(CasoRizoma4Error):
        validar_caso_id(valor)


def test_admin_lista_catalogo_rizoma4():
    resultado = empresas.listar_casos_disponibles("EMPRESA_A", usuario={"rol": "admin"})
    assert resultado["total"] == 2
    assert {c["caso_id"] for c in resultado["casos"]} == {"CASO_A", "CASO_B"}


def test_solo_admin_puede_asociar():
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        empresas.asociar_caso("EMPRESA_A", empresas.CasoRizoma4In(caso_id="CASO_A"), usuario={"rol": "aux_obra"})
    assert exc.value.status_code == 403


def test_admin_asocia_y_desasocia_sin_borrar_historial():
    entrada = empresas.CasoRizoma4In(caso_id="CASO_A")
    creada = empresas.asociar_caso("EMPRESA_A", entrada, usuario={"rol": "admin", "sub": "ADMIN_1"})
    assert creada["activo"] is True
    desactivada = empresas.desasociar_caso("EMPRESA_A", "CASO_A", usuario={"rol": "admin", "sub": "ADMIN_1"})
    assert desactivada["activo"] is False
    assert RepoFalso.datos[("EMPRESA_A", "CASO_A")]["caso_id"] == "CASO_A"


def test_no_asocia_un_caso_que_no_existe_en_rizoma4(monkeypatch):
    from fastapi import HTTPException

    class ClienteSinCaso:
        def listar_casos(self):
            return [{"caso_id": "CASO_OTRO"}]

    monkeypatch.setattr(empresas, "ClienteRizoma4", ClienteSinCaso)
    with pytest.raises(HTTPException) as exc:
        empresas.asociar_caso("EMPRESA_A", empresas.CasoRizoma4In(caso_id="CASO_A"), usuario={"rol": "admin"})
    assert exc.value.status_code == 404


def test_asiento_input_exige_caso_id():
    from pydantic import ValidationError
    from conta_rizoma4.api.schemas import AsientoIn

    with pytest.raises(ValidationError):
        AsientoIn(
            empresa_id="EMPRESA_A",
            codigo_acto="A_TEST",
            fecha="2026-01-01",
            concepto="Prueba",
            creado_por="operario",
            parametros={},
        )


def test_caso_id_forma_parte_de_metadatos_del_asiento():
    from datetime import date
    from conta_rizoma4.partida_doble.creacion import crear_asiento
    from conta_rizoma4.partida_doble.modelo import Linea

    asiento_a = crear_asiento(
        indice=0, fecha=date(2026, 1, 1), concepto="Prueba",
        lineas=[Linea("572", debe_centimos=100), Linea("100", haber_centimos=100)],
        metadatos={"codigo": "A_TEST", "caso_id": "CASO_A"},
    )
    asiento_b = crear_asiento(
        indice=0, fecha=date(2026, 1, 1), concepto="Prueba",
        lineas=[Linea("572", debe_centimos=100), Linea("100", haber_centimos=100)],
        metadatos={"codigo": "A_TEST", "caso_id": "CASO_B"},
    )
    assert asiento_a.hash != asiento_b.hash
