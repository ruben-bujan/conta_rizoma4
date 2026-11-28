"""Pruebas del adaptador PostgreSQL reversible del dominio."""


class ConexionPrueba:
    def __init__(self):
        self.sentencias = []
        self.parametros = []
        self.rollback_count = 0
        self.commit_count = 0
        self.closed = False

    def cursor(self):
        return CursorPrueba(self)

    def rollback(self):
        self.rollback_count += 1

    def commit(self):
        self.commit_count += 1

    def close(self):
        self.closed = True


class CursorPrueba:
    def __init__(self, conexion):
        self.conexion = conexion

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sentencia, parametros=None):
        self.conexion.sentencias.append(" ".join(sentencia.split()))
        self.conexion.parametros.append(parametros)


def test_ensayo_postgres_crea_correspondencias_y_revierte():
    from conta_rizoma4.dominio import ImportadorCorrespondenciasPostgres

    conexion = ConexionPrueba()
    importador = ImportadorCorrespondenciasPostgres(conexion=conexion)
    correspondencias, reporte = importador.ensayar_importacion("EMP-A", [
        {"empresa_id": "EMP-A", "indice": 1},
        {"empresa_id": "EMP-A", "indice": 2},
    ])

    assert len(correspondencias) == 2
    assert all(c.estado_migracion == "IMPORTADO_SIN_ACREDITACION_EPSTEMICA" for c in correspondencias)
    assert reporte["rollback"] is True
    assert reporte["persistido"] is False
    assert conexion.rollback_count == 1
    assert conexion.commit_count == 0


def test_confirmacion_postgres_no_modifica_asientos_heredados():
    from conta_rizoma4.dominio import ImportadorCorrespondenciasPostgres

    conexion = ConexionPrueba()
    importador = ImportadorCorrespondenciasPostgres(conexion=conexion)
    correspondencias = importador.confirmar_importacion("EMP-A", [
        {"empresa_id": "EMP-A", "indice": 7},
    ])

    assert [c.destino_id for c in correspondencias] == ["REP-EMP-A-7"]
    assert conexion.commit_count == 1
    assert conexion.rollback_count == 0


def test_importador_rechaza_indices_duplicados():
    from conta_rizoma4.dominio import ImportadorCorrespondenciasPostgres

    importador = ImportadorCorrespondenciasPostgres(conexion=ConexionPrueba())
    try:
        importador.confirmar_importacion("EMP-A", [
            {"empresa_id": "EMP-A", "indice": 1},
            {"empresa_id": "EMP-A", "indice": 1},
        ])
    except ValueError:
        return
    raise AssertionError("Los índices duplicados deben ser rechazados")


def test_importador_rechaza_asientos_de_otra_empresa():
    import pytest
    from conta_rizoma4.dominio import ImportadorCorrespondenciasPostgres

    importador = ImportadorCorrespondenciasPostgres(conexion=ConexionPrueba())
    with pytest.raises(ValueError, match="no pertenece"):
        importador.ensayar_importacion("EMP-A", [
            {"empresa_id": "EMP-B", "indice": 1},
        ])


def test_ensayo_postgres_revierte_tambien_si_falla_la_operacion():
    import pytest
    from conta_rizoma4.dominio import ImportadorCorrespondenciasPostgres

    class CursorFallido(CursorPrueba):
        def execute(self, sentencia, parametros=None):
            raise RuntimeError("fallo simulado")

    class ConexionFallida(ConexionPrueba):
        def cursor(self):
            return CursorFallido(self)

    conexion = ConexionFallida()
    importador = ImportadorCorrespondenciasPostgres(conexion=conexion)
    with pytest.raises(RuntimeError, match="simulado"):
        importador.ensayar_importacion("EMP-A", [
            {"empresa_id": "EMP-A", "indice": 1},
        ])
    assert conexion.rollback_count == 1
    assert conexion.commit_count == 0


def test_verificacion_dual_permite_activacion_solo_si_todo_coincide():
    from conta_rizoma4.dominio import crear_correspondencia_asiento, verificar_dual

    heredado = [{
        "empresa_id": "EMP-A", "indice": 1, "fecha": "2025-04-12",
        "concepto": "Factura", "hash": "ABC", "estado": "APROBADO",
        "total_debe": 100, "total_haber": 100,
    }]
    postgres = [dict(heredado[0])]
    correspondencias = [crear_correspondencia_asiento("EMP-A", 1, "REP-EMP-A-1")]

    resultado = verificar_dual(heredado, postgres, correspondencias)

    assert resultado.reversible
    assert resultado.activacion_permitida


def test_verificacion_dual_bloquea_por_diferencia():
    from conta_rizoma4.dominio import crear_correspondencia_asiento, verificar_dual

    heredado = [{
        "empresa_id": "EMP-A", "indice": 1, "fecha": "2025-04-12",
        "concepto": "Factura", "hash": "ABC", "estado": "APROBADO",
    }]
    postgres = [dict(heredado[0], hash="XYZ")]
    correspondencias = [crear_correspondencia_asiento("EMP-A", 1, "REP-EMP-A-1")]

    resultado = verificar_dual(heredado, postgres, correspondencias)

    assert not resultado.reversible
    assert not resultado.activacion_permitida
    assert any(d.campo == "hash" for d in resultado.diferencias)


def test_verificacion_dual_bloquea_sin_correspondencia():
    from conta_rizoma4.dominio import verificar_dual

    heredado = [{"empresa_id": "EMP-A", "indice": 1, "hash": "ABC"}]
    postgres = [dict(heredado[0])]

    resultado = verificar_dual(heredado, postgres)

    assert not resultado.activacion_permitida
    assert any(d.campo == "correspondencia" for d in resultado.diferencias)


def test_verificacion_dual_detecta_claves_y_correspondencias_duplicadas():
    from conta_rizoma4.dominio import crear_correspondencia_asiento, verificar_dual

    asiento = {"empresa_id": "EMP-A", "indice": 1, "hash": "H-1"}
    resultado = verificar_dual(
        [asiento, dict(asiento)],
        [asiento, dict(asiento)],
        [
            crear_correspondencia_asiento("EMP-A", 1, "REP-1"),
            crear_correspondencia_asiento("EMP-A", 1, "REP-2"),
        ],
    )

    campos = {d.campo for d in resultado.diferencias}
    assert "clave_duplicada" in campos
    assert "correspondencia_duplicada" in campos
    assert not resultado.activacion_permitida


def test_verificacion_dual_compara_lineas_documentos_y_rectificaciones():
    from conta_rizoma4.dominio import crear_correspondencia_asiento, verificar_dual

    heredado = [{
        "empresa_id": "EMP-A", "indice": 4, "lineas": [{"cuenta": "430", "debe": 100}],
        "documentos": ["DOC-1"], "rectificaciones": [],
    }]
    importado = [{
        "empresa_id": "EMP-A", "indice": 4, "lineas": [{"cuenta": "430", "debe": 90}],
        "documentos": ["DOC-2"], "rectificaciones": ["REC-1"],
    }]
    resultado = verificar_dual(
        heredado, importado, [crear_correspondencia_asiento("EMP-A", 4, "REP-4")],
    )

    assert {d.campo for d in resultado.diferencias} >= {
        "lineas", "documentos", "rectificaciones",
    }


def test_verificacion_dual_detecta_correspondencia_sobrante():
    from conta_rizoma4.dominio import crear_correspondencia_asiento, verificar_dual

    resultado = verificar_dual(
        [{"empresa_id": "EMP-A", "indice": 1}],
        [{"empresa_id": "EMP-A", "indice": 1}],
        [
            crear_correspondencia_asiento("EMP-A", 1, "REP-1"),
            crear_correspondencia_asiento("EMP-A", 2, "REP-2"),
        ],
    )
    assert any(d.campo == "correspondencia_sobrante" for d in resultado.diferencias)


def test_verificacion_dual_bloquea_correspondencia_acreditada():
    from conta_rizoma4.dominio import crear_correspondencia_asiento, verificar_dual

    correspondencia = crear_correspondencia_asiento("EMP-A", 1, "REP-1")
    correspondencia = type(correspondencia)(
        origen_tipo=correspondencia.origen_tipo,
        origen_empresa=correspondencia.origen_empresa,
        origen_indice=correspondencia.origen_indice,
        destino_tipo=correspondencia.destino_tipo,
        destino_id=correspondencia.destino_id,
        estado_migracion="ACREDITADO",
    )
    resultado = verificar_dual(
        [{"empresa_id": "EMP-A", "indice": 1}],
        [{"empresa_id": "EMP-A", "indice": 1}],
        [correspondencia],
    )
    assert any(d.campo == "estado_migracion" for d in resultado.diferencias)
    assert not resultado.activacion_permitida
