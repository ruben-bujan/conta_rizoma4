"""Pruebas de bloqueos de seguridad INCIVSA."""


def test_ensayo_sin_persistencia_valido():
    from .bloqueos import validar_ensayo_sin_persistencia

    validar_ensayo_sin_persistencia(
        persistir=False,
        generar_placeholder=False,
        actualizar_heredado=False,
    )


def test_persistencia_bloqueada():
    from .bloqueos import ActivacionPilotoBloqueada, validar_ensayo_sin_persistencia

    try:
        validar_ensayo_sin_persistencia(True, False, False)
    except ActivacionPilotoBloqueada:
        return
    raise AssertionError("La persistencia debe bloquearse")


def test_placeholder_bloqueado():
    from .bloqueos import ActivacionPilotoBloqueada, validar_ensayo_sin_persistencia

    try:
        validar_ensayo_sin_persistencia(False, True, False)
    except ActivacionPilotoBloqueada:
        return
    raise AssertionError("Los placeholders deben bloquearse")


def test_modificacion_asiento_bloqueada():
    from .bloqueos import ActivacionPilotoBloqueada, validar_ensayo_sin_persistencia

    try:
        validar_ensayo_sin_persistencia(False, False, True)
    except ActivacionPilotoBloqueada:
        return
    raise AssertionError("Modificar asientos heredados debe bloquearse")


def test_actuaciones_extraordinarias_bloquean_persistencia():
    from .bloqueos import ActivacionPilotoBloqueada, validar_actuaciones_extraordinarias_revisadas

    try:
        validar_actuaciones_extraordinarias_revisadas(False)
    except ActivacionPilotoBloqueada:
        return
    raise AssertionError("La persistencia extraordinaria debe bloquearse")
