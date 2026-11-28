from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Depends, HTTPException

from ..dominio import Actor, ErrorDominio, Rol
from ..dominio.adaptadores.repositorio_postgres import RepositorioPermisosEvento
from .routers.auth import requerir_usuario

_ROLES_DOMINIO: dict[str, Rol] = {
    "aux_obra": Rol.AUXILIAR,
    "visador": Rol.JEFE_CONTABILIDAD,
    "aprobador": Rol.SUBDIRECTOR,
    "admin": Rol.ADMIN,
}


def rol_dominio(rol_api: str) -> Rol:
    rol = _ROLES_DOMINIO.get(rol_api)
    if rol is None:
        raise HTTPException(status_code=403, detail="Rol sin mapeo al dominio contable")
    return rol


def actor_actual(usuario: dict = Depends(requerir_usuario)) -> Actor:
    actor_id = (
        usuario.get("actor_id")
        or usuario.get("usuario_id")
        or usuario.get("sub")
    )
    if not actor_id:
        raise HTTPException(status_code=401, detail="Token sin identidad de actor")
    return Actor(
        actor_id=str(actor_id),
        nombre=str(usuario.get("nombre") or actor_id),
        rol=rol_dominio(str(usuario.get("rol") or "")),
    )


def usuario_con_competencia(competencia: str, *roles_api: str):
    """Exige rol API y competencia del núcleo con permisos desde `dominio_evento`."""

    def dependencia(usuario: dict = Depends(requerir_usuario)) -> dict:
        rol_api = str(usuario.get("rol") or "")
        if roles_api and rol_api not in roles_api:
            raise HTTPException(status_code=403, detail="Rol sin acceso a la operación")
        rol = rol_dominio(rol_api)
        if rol is Rol.ADMIN:
            return usuario

        actor_id = (
            usuario.get("actor_id")
            or usuario.get("usuario_id")
            or usuario.get("sub")
        )
        if not actor_id:
            raise HTTPException(status_code=401, detail="Token sin identidad de actor")
        empresa_id = usuario.get("empresa_id")
        if not empresa_id:
            raise HTTPException(status_code=403, detail="Token sin empresa para la competencia")

        momento = datetime.now(timezone.utc)
        repositorio = RepositorioPermisosEvento()
        nucleo = repositorio.nucleo_para_entidad(str(empresa_id), momento)
        actor = Actor(
            actor_id=str(actor_id),
            nombre=str(usuario.get("nombre") or actor_id),
            rol=rol,
        )
        if rol is Rol.AUXILIAR:
            for permiso in nucleo.permisos.values():
                if (
                    permiso.beneficiario_id == actor.actor_id
                    and permiso.competencia == competencia
                    and permiso.alcance in (str(empresa_id), "*")
                    and permiso.revocada_en is None
                    and permiso.otorgada_en <= momento
                    and (permiso.vigente_hasta is None or momento <= permiso.vigente_hasta)
                ):
                    actor.rol = Rol.OPERARIO
                    break
        nucleo.actores[actor.actor_id] = actor
        try:
            nucleo.verificar_competencia(
                actor.actor_id, competencia, str(empresa_id), momento,
            )
        except ErrorDominio as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        return usuario

    return dependencia
