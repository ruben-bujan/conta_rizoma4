# -*- coding: utf-8 -*-
"""Endpoints de asientos corregidos para compatibilidad estricta con AsientoOut (H-10 y H-11)."""
from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

from ..schemas import AsientoIn, AsientoOut, LineaOut
from ...partida_doble import RepositorioAsiento
from ...partida_doble.backend import BackendPostgres
from ...actos.catalogo import obtener as obtener_acto
from ...custodia.casos_rizoma4 import RepositorioCasoRizoma4, CasoRizoma4Error
from .auth import requerir_usuario, requerir_roles
from ..deps import usuario_con_competencia


router = APIRouter(prefix="/asientos", tags=["asientos"])


@router.get("", response_model=list[AsientoOut])
def listar_asientos(
    usuario: dict = Depends(requerir_usuario),
    empresa_id: Optional[str] = Query(None),
    desde: Optional[int] = None,
    hasta: Optional[int] = None,
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    limite: int = 100,
):
    target_empresa = empresa_id if (usuario.get("rol") == "admin" and empresa_id) else usuario.get("empresa_id")
    if not target_empresa:
        raise HTTPException(status_code=403, detail="Usuario sin empresa asociada en el token")
    try:
        repo = RepositorioAsiento(target_empresa)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # H-11: Obtener los listados asegurando que se recuperen las líneas completas
    # para que coincidan estrictamente con el response_model=list[AsientoOut].
    if estado:
        headers = repo.listar_por_estado(estado, limite=limite)
    else:
        headers = repo.listar(indice_desde=desde, indice_hasta=hasta, limite=limite)

    resultado = []
    for h in headers:
        # Recuperar el asiento completo incluyendo sus líneas desglosadas
        completo = repo.obtener(h["indice"])
        if completo:
            resultado.append(completo)

    return resultado


@router.get("/{indice}", response_model=AsientoOut)
def obtener_asiento(
    indice: int,
    usuario: dict = Depends(requerir_usuario),
):
    empresa_id = usuario.get("empresa_id")
    if not empresa_id:
        raise HTTPException(status_code=403, detail="Usuario sin empresa asociada en el token")
    try:
        repo = RepositorioAsiento(empresa_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    d = repo.obtener(indice)
    if d is None:
        raise HTTPException(status_code=404, detail="Asiento no encontrado")
    return d


@router.post("", response_model=AsientoOut, status_code=201)
def crear_asiento(
    entrada: AsientoIn,
    usuario: dict = Depends(usuario_con_competencia("ASIENTO_DIARIO", "admin", "aux_obra")),
):
    empresa_id = usuario.get("empresa_id")
    if not empresa_id:
        raise HTTPException(status_code=403, detail="Usuario sin empresa asociada en el token")

    # Forzar que la empresa del asiento coincida de forma segura con la del token
    entrada.empresa_id = empresa_id
    actor_id = str(usuario.get("sub") or usuario.get("usuario_id") or "")
    if not actor_id:
        raise HTTPException(status_code=401, detail="El usuario autenticado no tiene identidad")
    # Nunca aceptar del cuerpo una identidad creadora declarada por el cliente.
    entrada.creado_por = actor_id

    if entrada.obra_id:
        from ...custodia.repositorios import RepositorioObra
        obra = RepositorioObra().obtener(entrada.obra_id)
        if obra is None or obra.get("empresa_id") != empresa_id:
            raise HTTPException(status_code=404, detail="Obra no encontrada para esta empresa")

    if entrada.documento_ref or entrada.documentos_refs:
        from ...custodia.repositorios import RepositorioDocumento
        repo_documentos = RepositorioDocumento()
        hashes = set(entrada.documentos_refs)
        if entrada.documento_ref:
            hashes.add(entrada.documento_ref)
        for hash_cas in hashes:
            if repo_documentos.obtener_por_hash(empresa_id, hash_cas) is None:
                raise HTTPException(status_code=404, detail="Documento no encontrado para esta empresa")

    try:
        repo = RepositorioAsiento(entrada.empresa_id)
        caso_id = entrada.caso_id
        if not RepositorioCasoRizoma4().esta_asociado(entrada.empresa_id, caso_id):
            raise HTTPException(
                status_code=422,
                detail=(f"El caso RIZOMA4 {caso_id!r} no está asociado o está "
                        f"desactivado para la empresa {entrada.empresa_id!r}"),
            )
    except CasoRizoma4Error as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        _, fn = obtener_acto(entrada.codigo_acto)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 1. Si hay lease, validarlo rigurosamente (H-12)
    lease = None
    if entrada.lease_id:
        from ...custodia.repositorios import RepositorioLease
        from ...custodia.modelo import CustodiaError
        from datetime import datetime, timezone

        try:
            lease = RepositorioLease().obtener(entrada.lease_id)
        except Exception:
            lease = None

        if lease is None:
            raise HTTPException(status_code=409, detail="Lease no encontrado")

        if lease["estado"] != "CONCEDIDO":
            raise HTTPException(
                status_code=409,
                detail=f"Lease en estado {lease['estado']}, se requiere CONCEDIDO",
            )

        # H-12: Comprobación estricta de pertenencia multiempresa y obra
        if lease.get("empresa_id") and lease["empresa_id"] != entrada.empresa_id:
            raise HTTPException(
                status_code=403,
                detail="El lease no pertenece a la empresa autenticada",
            )

        if entrada.obra_id and lease.get("obra_id") and lease["obra_id"] != entrada.obra_id:
            raise HTTPException(
                status_code=409,
                detail="El lease no corresponde a la obra especificada en la petición",
            )

        if entrada.creado_por and lease.get("operario") and lease["operario"] != entrada.creado_por:
            raise HTTPException(
                status_code=409,
                detail="El lease no pertenece al operario emisor",
            )

        # H-12: Comprobación de vigencia / expiración si el campo existe en el modelo de lease
        expira_en = lease.get("expira_en")
        if expira_en:
            if isinstance(expira_en, str):
                expira_en = datetime.fromisoformat(expira_en)
            # Asegurar comparación UTC consciente
            if expira_en.tzinfo is None:
                expira_en = expira_en.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > expira_en:
                raise HTTPException(
                    status_code=409,
                    detail="El lease ha expirado",
                )

    # 2. Calcular índice y hash previo.
    # El índice es SIEMPRE el siguiente libre por orden de registro. Tras elegir
    # la Ruta B (cadena ordenada por índice), la posición en la cadena ES el
    # índice: no admite huecos ni reservas de posición por adelantado.
    # Mismo criterio que backend.py, cli_pd.py y los demos.
    ultimo_idx = repo.ultimo_indice()
    indice = ultimo_idx + 1
    ultimo_data = repo.obtener(ultimo_idx) if ultimo_idx >= 0 else None
    from ...operativo.asiento import GENESIS
    hash_previo = ultimo_data["hash"] if ultimo_data else GENESIS

    # 3. Crear acto
    params = dict(entrada.parametros)
    params.update({
        "indice": indice,
        "hash_previo": hash_previo,
        "fecha": entrada.fecha,
        "concepto": entrada.concepto,
    })
    try:
        acto = fn(**params, creado_por=entrada.creado_por)
    except TypeError:
        acto = fn(**params)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 4. Incorporar el destino investigador a los metadatos antes de calcular
    # la huella: caso_id queda protegido por el hash encadenado del asiento.
    from ...partida_doble.creacion import crear_asiento
    metadatos = dict(acto.metadatos or {})
    metadatos["caso_id"] = caso_id
    acto = crear_asiento(
        indice=acto.indice,
        fecha=acto.fecha,
        concepto=acto.concepto,
        lineas=list(acto.lineas),
        hash_previo=acto.hash_previo,
        metadatos=metadatos,
    )

    # 5. Persistir asiento y destino en la misma inserción.
    from ...partida_doble.persistencia import guardar_asiento
    try:
        guardar_asiento(acto, empresa_id=entrada.empresa_id, caso_id=caso_id)
    except Exception as exc:
        # La FK/trigger es la última barrera frente a una desasociación
        # concurrente entre la validación API y la inserción.
        from psycopg.errors import ForeignKeyViolation
        if isinstance(exc, ForeignKeyViolation):
            raise HTTPException(
                status_code=409,
                detail="La asociación empresa-caso dejó de estar activa antes de guardar el asiento",
            ) from exc
        raise

    # 5. Actualizar campos de custodia y registrar relación N:M en asiento_documentos (H-15)
    import psycopg
    from ...partida_doble.persistencia import PG_URL

    docs_a_vincular = set(entrada.documentos_refs)
    if entrada.documento_ref:
        docs_a_vincular.add(entrada.documento_ref)

    with psycopg.connect(PG_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE asiento_contable
                SET obra_id = %s, operario_creador = %s,
                    lease_id = %s, estado = %s,
                    documento_ref = %s
                WHERE empresa_id = %s AND indice = %s
                """,
                (entrada.obra_id, entrada.creado_por,
                 entrada.lease_id, "BORRADOR",
                 entrada.documento_ref, entrada.empresa_id, indice),
            )

            # Inserción en la tabla puente N:M asiento_documentos (H-15)
            for doc_hash in docs_a_vincular:
                cur.execute(
                    """
                    INSERT INTO asiento_documentos (empresa_id, asiento_indice, documento_id)
                    SELECT %s, %s, id FROM documentos
                    WHERE empresa_id = %s AND hash_cas = %s
                    ON CONFLICT DO NOTHING
                    """,
                    (entrada.empresa_id, indice, entrada.empresa_id, doc_hash)
                )
        conn.commit()

    # 6. Marcar lease como USADO
    if lease:
        from ...custodia.repositorios import RepositorioLease
        RepositorioLease().marcar_usado(entrada.lease_id)

    return {
        "indice": acto.indice,
        "caso_id": caso_id,
        "fecha": acto.fecha,
        "concepto": acto.concepto,
        "lineas": [
            {
                "cuenta_pgc": l.cuenta_pgc,
                "debe_centimos": l.debe_centimos,
                "haber_centimos": l.haber_centimos,
                "parrafo_pgc_id": l.parrafo_pgc_id,
                "concepto_linea": l.concepto_linea,
            }
            for l in acto.lineas
        ],
        "hash_previo": acto.hash_previo,
        "hash": acto.hash,
        "metadatos": acto.metadatos,
    }


class RizomizarIn(BaseModel):
    ok: bool
    alerta: Optional[str] = None
    documento_ref: Optional[str] = None


@router.post("/{indice}/visar")
def visar(
    indice: int,
    usuario: dict = Depends(usuario_con_competencia("ASIENTO_VISAR", "admin", "visador")),
    empresa_id: Optional[str] = Query(None),
):
    target_empresa = empresa_id if (usuario.get("rol") == "admin" and empresa_id) else usuario.get("empresa_id")
    if not target_empresa:
        raise HTTPException(status_code=403, detail="Usuario sin empresa asociada en el token")

    import psycopg
    from ...partida_doble.persistencia import PG_URL
    with psycopg.connect(PG_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT estado, operario_creador FROM asiento_contable "
                "WHERE empresa_id = %s AND indice = %s FOR UPDATE",
                (target_empresa, indice),
            )
            row = cur.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Asiento no encontrado")
            if row[0] != "BORRADOR":
                raise HTTPException(
                    status_code=409,
                    detail=f"Asiento en estado {row[0]}, no BORRADOR",
                )
            actor_id = usuario.get("sub") or usuario.get("usuario_id")
            if actor_id == row[1]:
                raise HTTPException(status_code=409, detail="El creador no puede visar su propio asiento")
            try:
                from ...integracion.attestia_client import AttestiaClient
                firma = AttestiaClient().firmar(f"asiento:{target_empresa}:{indice}:{actor_id}")
                firma_hex = firma.get("firma_hex")
            except Exception:
                firma_hex = None
            cur.execute(
                "UPDATE asiento_contable SET estado = 'VISADO', "
                "operario_visador = %s "
                "WHERE empresa_id = %s AND indice = %s AND estado = 'BORRADOR'",
                (actor_id, target_empresa, indice),
            )
        conn.commit()
    return {"ok": True, "estado": "VISADO", "firma_hex": firma_hex}


@router.post("/{indice}/aprobar")
def aprobar(
    indice: int,
    usuario: dict = Depends(usuario_con_competencia("ASIENTO_APROBAR", "admin", "aprobador")),
    empresa_id: Optional[str] = Query(None),
):
    target_empresa = empresa_id if (usuario.get("rol") == "admin" and empresa_id) else usuario.get("empresa_id")
    if not target_empresa:
        raise HTTPException(status_code=403, detail="Usuario sin empresa asociada en el token")

    import psycopg
    from ...partida_doble.persistencia import PG_URL
    with psycopg.connect(PG_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT estado, operario_visador, operario_creador FROM asiento_contable "
                "WHERE empresa_id = %s AND indice = %s FOR UPDATE",
                (target_empresa, indice),
            )
            row = cur.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Asiento no encontrado")
            if row[0] != "VISADO":
                raise HTTPException(
                    status_code=409,
                    detail=f"Asiento en estado {row[0]}, no VISADO",
                )
            actor_id = usuario.get("sub") or usuario.get("usuario_id")
            if actor_id in {row[1], row[2]}:
                raise HTTPException(status_code=409, detail="El aprobador debe ser distinto del creador y del visador")
            cur.execute(
                "UPDATE asiento_contable SET estado = 'APROBADO', "
                "operario_aprobador = %s "
                "WHERE empresa_id = %s AND indice = %s AND estado = 'VISADO'",
                (actor_id, target_empresa, indice),
            )
        conn.commit()
    return {"ok": True, "estado": "APROBADO"}


@router.post("/{indice}/rizomizar")
def rizomizar(
    indice: int,
    entrada: RizomizarIn,
    usuario: dict = Depends(requerir_roles("admin")),
    empresa_id: Optional[str] = Query(None),
):
    target_empresa = empresa_id if (usuario.get("rol") == "admin" and empresa_id) else usuario.get("empresa_id")
    if not target_empresa:
        raise HTTPException(status_code=403, detail="Usuario sin empresa asociada en el token")

    import psycopg
    from ...partida_doble.persistencia import PG_URL
    with psycopg.connect(PG_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT estado FROM asiento_contable "
                "WHERE empresa_id = %s AND indice = %s",
                (target_empresa, indice),
            )
            row = cur.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Asiento no encontrado")
            if row[0] != "APROBADO":
                raise HTTPException(
                    status_code=409,
                    detail=f"Asiento en estado {row[0]}, no APROBADO",
                )
            if entrada.ok:
                nuevo_estado = "RIZOMIZADO"
                alerta = None
            else:
                nuevo_estado = "EN_CUARENTENA"
                alerta = entrada.alerta or "Rizomización fallida"
            cur.execute(
                "UPDATE asiento_contable SET estado = %s, alerta = %s, "
                "documento_ref = COALESCE(%s, documento_ref) "
                "WHERE empresa_id = %s AND indice = %s",
                (nuevo_estado, alerta, entrada.documento_ref,
                 target_empresa, indice),
            )
        conn.commit()
    return {"ok": True, "estado": "RIZOMIZADO" if entrada.ok else "EN_CUARENTENA"}


    # 2. Calcular índice y hash previo.
    # El índice es SIEMPRE el siguiente libre por orden de registro. Tras elegir
    # la Ruta B (cadena ordenada por índice), la posición en la cadena ES el
    # índice: no admite huecos ni reservas de posición por adelantado.
    # Mismo criterio que backend.py, cli_pd.py y los demos.
    ultimo_idx = repo.ultimo_indice()
    indice = ultimo_idx + 1
    ultimo_data = repo.obtener(ultimo_idx) if ultimo_idx >= 0 else None
    from ...operativo.asiento import GENESIS
    hash_previo = ultimo_data["hash"] if ultimo_data else GENESIS
