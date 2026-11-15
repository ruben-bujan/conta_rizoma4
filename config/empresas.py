# conta_rizoma4/config/empresas.py

@dataclass(frozen=True)
class ConfigEmpresa:
    empresa_id: str
    nombre: str
    moneda_funcional: str      # ISO 4217
    marco_contable: str        # PGC_ES, NIIF, US_GAAP, ...
    pais: str                  # ISO 3166-1 alpha-2
    grupo: str                 # a qué grupo pertenece
    participacion_matriz: float  # % (0-100)
    ejercicio_inicio: str      # "MM-DD"
    ejercicio_fin: str         # "MM-DD"


class ConfigError(Exception):
    """Error en la configuración de empresas."""


def cargar_config(path: Path) -> dict[str, ConfigEmpresa]:
    """Carga el fichero. Valida. Falla si hay error."""
    # Validaciones:
    # - empresa_id único
    # - moneda_funcional ISO 4217 válida
    # - marco_contable en marcos_contables
    # - participacion_matriz en [0, 100]
    # - grupo no vacío
    # - ejercicio_inicio < ejercicio_fin (o wrap si MM-DD)
    ...