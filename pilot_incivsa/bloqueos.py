"""Guardas de seguridad del ensayo piloto INCIVSA."""


OPERACIONES_PROHIBIDAS = (
    "DELETE",
    "TRUNCATE",
    "DROP",
    "ALTER",
    "UPDATE_ASIENTO_HEREDADO",
    "GENERAR_PLACEHOLDER_DOCUMENTAL",
    "PERSISTIR_POSTGRESQL",
    "ACTIVAR_RIZOMA4",
)


class ActivacionPilotoBloqueada(RuntimeError):
    pass


def validar_ensayo_sin_persistencia(
    persistir: bool,
    generar_placeholder: bool,
    actualizar_heredado: bool,
) -> None:
    if persistir:
        raise ActivacionPilotoBloqueada("La persistencia está prohibida en el ensayo")
    if generar_placeholder:
        raise ActivacionPilotoBloqueada("Los placeholders no son prueba documental")
    if actualizar_heredado:
        raise ActivacionPilotoBloqueada("No se permite modificar asientos heredados")


def validar_actuaciones_extraordinarias_revisadas(revisadas: bool) -> None:
    if not revisadas:
        raise ActivacionPilotoBloqueada(
            "Persistencia bloqueada: actuaciones judiciales y administrativas "
            "extraordinarias pendientes de revisión"
        )
