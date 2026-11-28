import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import ValidationError

from conta_rizoma4.api.routers import auth


def test_registro_no_admite_rol_admin_ni_empresa_en_payload():
    with pytest.raises(ValidationError):
        auth.RegistroIn(
            usuario_id="U1", email="u@example.org", password="password-12345",
            nombre="Usuario", rol="admin", empresa_id="EMP-OTRA",
        )


def test_requerir_rol_bloquea_usuario_sin_funcion():
    dependencia = auth.requerir_roles("aprobador")
    with pytest.raises(HTTPException) as error:
        dependencia(usuario={"rol": "aux_obra"})
    assert error.value.status_code == 403


def test_token_no_conserva_rol_revocado(monkeypatch):
    class Cursor:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def execute(self, sql, params):
            self.params = params
        def fetchone(self):
            return ("U1", "aux_obra", "EMP-1", True)

    class Conn:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def cursor(self):
            return Cursor()

    monkeypatch.setattr(auth, "verificar_token", lambda token: {
        "sub": "U1", "rol": "admin", "empresa_id": "EMP-PRIVILEGIADA",
    })
    monkeypatch.setattr(auth, "_conn", Conn)
    cred = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")
    usuario = auth.usuario_actual(cred)
    assert usuario == {
        "sub": "U1", "actor_id": "U1", "usuario_id": "U1",
        "rol": "aux_obra", "empresa_id": "EMP-1",
    }


def test_listado_empresas_filtra_por_empresa_del_usuario(monkeypatch):
    from types import SimpleNamespace
    from conta_rizoma4.api.routers import empresas

    class Empresa:
        def __init__(self, empresa_id):
            self.empresa_id = empresa_id
        def a_dict(self):
            return {"empresa_id": self.empresa_id}

    monkeypatch.setattr(empresas, "get_config", lambda: SimpleNamespace(
        empresas={"EMP-1": Empresa("EMP-1"), "EMP-2": Empresa("EMP-2")},
    ))
    assert empresas.listar_empresas(usuario={"rol": "aux_obra", "empresa_id": "EMP-2"}) == [
        {"empresa_id": "EMP-2"}
    ]


def test_requerir_admin_bloquea_roles_operativos():
    requisito_admin = auth.requerir_roles("admin")
    with pytest.raises(HTTPException) as error:
        requisito_admin(usuario={"rol": "aux_obra", "empresa_id": "EMP-1"})
    assert error.value.status_code == 403
    assert requisito_admin(usuario={"rol": "admin", "empresa_id": "EMP-1"})["rol"] == "admin"


def test_mapeo_roles_api_a_dominio():
    from conta_rizoma4.api import deps
    from conta_rizoma4.dominio import Rol

    assert deps.rol_dominio("aux_obra") is Rol.AUXILIAR
    assert deps.rol_dominio("visador") is Rol.JEFE_CONTABILIDAD
    assert deps.rol_dominio("aprobador") is Rol.SUBDIRECTOR
    assert deps.rol_dominio("admin") is Rol.ADMIN
    with pytest.raises(HTTPException) as error:
        deps.rol_dominio("desconocido")
    assert error.value.status_code == 403


def test_actor_actual_con_rol_de_dominio():
    from conta_rizoma4.api import deps
    from conta_rizoma4.dominio import Rol

    actor = deps.actor_actual({
        "actor_id": "U1", "rol": "visador", "empresa_id": "EMP-1",
    })
    assert actor.actor_id == "U1"
    assert actor.rol is Rol.JEFE_CONTABILIDAD
    assert actor.puede_ejecutar(Rol.JEFE_CONTABILIDAD)


def test_token_incluye_actor_id():
    from conta_rizoma4.auth import crear_token, verificar_token

    payload = verificar_token(crear_token("U1", "aux_obra", "EMP-1"))
    assert payload["actor_id"] == "U1"


def test_solicitud_lease_limita_duracion_y_no_admite_campos_extra():
    from conta_rizoma4.api.routers.leases import LeaseSolicitarIn

    with pytest.raises(ValidationError):
        LeaseSolicitarIn(
            empresa_id="EMP-1", operario="OP-1", duracion_min=1441,
        )
    with pytest.raises(ValidationError):
        LeaseSolicitarIn(
            empresa_id="EMP-1", operario="OP-1", rol="admin",
        )
