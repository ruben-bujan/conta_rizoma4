# -*- coding: utf-8 -*-
"""Tests de JustificacionInterna."""
from datetime import date

import pytest

from conta_rizoma4.operativo.asiento import GENESIS
from conta_rizoma4.operativo.justificacion_interna import (
    JustificacionInterna,
    crear_justificacion_interna,
    guardar_justificacion_interna,
)


class TestCrear:
    def test_justificacion_basica(self):
        j = crear_justificacion_interna(
            indice=0, fecha=date(2025, 3, 1),
            cuenta_pgc="4308",
            importe_centimos=50_000,
            concepto="Obra ejecutada marzo",
            creado_por="rubén",
            obra_ref="OBRA-2025-01",
        )
        assert isinstance(j, JustificacionInterna)
        assert j.hash_previo == GENESIS
        assert j.obra_ref == "OBRA-2025-01"
        assert len(j.hash) == 64

    def test_importe_debe_ser_int(self):
        with pytest.raises(TypeError):
            crear_justificacion_interna(
                indice=0, fecha=date(2025, 1, 1),
                cuenta_pgc="4308", importe_centimos=500.0,
                concepto="X", creado_por="rubén",
            )


class TestPersistencia:
    def test_guardar(self):
        j = crear_justificacion_interna(
            indice=9000, fecha=date(2025, 6, 15),
            cuenta_pgc="4308", importe_centimos=50_000,
            concepto="Test persistencia", creado_por="rubén",
            obra_ref="OBRA-TEST",
        )
        guardar_justificacion_interna(j)