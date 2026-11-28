from datetime import date, datetime, timezone

import pytest

from conta_rizoma4.consolidacion import (
    BalanceIndividual,
    ConsolidacionError,
    EliminacionConsolidacion,
    RelacionParticipacion,
    RepositorioConsolidacionMemoria,
)


CIERRE = date(2025, 12, 31)
T1 = datetime(2026, 1, 10, tzinfo=timezone.utc)
T2 = datetime(2026, 2, 10, tzinfo=timezone.utc)


def _registro_base():
    repo = RepositorioConsolidacionMemoria()
    repo.registrar_relacion(RelacionParticipacion("M", "F", 80, date(2025, 1, 1), conocida_desde=T1))
    repo.registrar_balance(BalanceIndividual("M", CIERRE, {"572": 1000, "100": -1000}, 100, T1))
    repo.registrar_balance(BalanceIndividual("F", CIERRE, {"572": 500, "100": -500}, 50, T1))
    return repo


def test_consolida_saldos_y_atribuye_minoritarios():
    repo = _registro_base()
    resultado = repo.consolidar("G", "M", CIERRE, T1)
    assert resultado.empresas == ("F", "M")
    assert resultado.saldos_consolidados == {"572": 1500, "100": -1500}
    assert resultado.resultado_grupo == 150
    assert resultado.resultado_matriz == 140
    assert resultado.resultado_minoritarios == 10
    assert resultado.cuadra


def test_eliminacion_sigue_como_propuesta_hasta_autorizacion_y_reconstruye():
    repo = _registro_base()
    repo.proponer_eliminacion(EliminacionConsolidacion(
        "E1", "G", CIERRE,
        {"M": {"440": -100}, "F": {"400": 100}},
        "Saldo recíproco contrastado", ("DOC-1",), "actor-proponente", T1,
    ))
    antes = repo.consolidar("G", "M", CIERRE, T1)
    assert len(antes.eliminaciones_propuestas) == 1
    assert not antes.eliminaciones_aplicadas
    assert "440" not in antes.saldos_consolidados

    repo.autorizar_eliminacion("E1", "actor-autorizador", "AUT-1", T2)
    reconstruido = repo.consolidar("G", "M", CIERRE, T1)
    actual = repo.consolidar("G", "M", CIERRE, T2)
    assert not reconstruido.eliminaciones_aplicadas
    assert len(actual.eliminaciones_aplicadas) == 1
    assert actual.saldos_consolidados["440"] == -100
    assert actual.saldos_consolidados["400"] == 100
    assert actual.cuadra


def test_exige_balance_de_todas_las_entidades_del_grupo():
    repo = RepositorioConsolidacionMemoria()
    repo.registrar_relacion(RelacionParticipacion("M", "F", 100, date(2025, 1, 1), conocida_desde=T1))
    with pytest.raises(ConsolidacionError, match="Falta balance"):
        repo.consolidar("G", "M", CIERRE, T1)


def test_no_acepta_autorizacion_sin_propuesta():
    repo = _registro_base()
    with pytest.raises(ConsolidacionError, match="No existe una propuesta"):
        repo.autorizar_eliminacion("NO", "actor", "AUT", T2)


def test_cambio_de_participacion_reconstruye_por_fecha_de_conocimiento():
    repo = _registro_base()
    repo.finalizar_relacion("M", "F", date(2025, 7, 1), T2)
    repo.registrar_relacion(RelacionParticipacion(
        "M", "F", 60, date(2025, 7, 1), conocida_desde=T2,
    ))
    historico = repo.consolidar("G", "M", CIERRE, T1)
    conocido = repo.consolidar("G", "M", CIERRE, T2)
    assert historico.participaciones_indirectas["F"] == 80
    assert conocido.participaciones_indirectas["F"] == 60
    assert historico.resultado_minoritarios == 10
    assert conocido.resultado_minoritarios == 20


def test_eliminacion_autorizada_de_resultado_ajusta_resultado_y_minoritarios():
    repo = _registro_base()
    repo.proponer_eliminacion(EliminacionConsolidacion(
        "E-PYG", "G", CIERRE,
        {"M": {"700": 20, "300": -20}},
        "Margen intragrupo no realizado", ("DOC-2",), "proponente", T1,
    ))
    repo.autorizar_eliminacion("E-PYG", "autorizador", "AUT-2", T2)
    resultado = repo.consolidar("G", "M", CIERRE, T2)
    assert resultado.resultado_grupo == 130
    assert resultado.resultado_matriz == 120
    assert resultado.resultado_minoritarios == 10
    assert resultado.cuadra
