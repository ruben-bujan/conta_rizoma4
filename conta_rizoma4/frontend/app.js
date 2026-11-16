// Estado del flujo
const estado = {
  obraId: null,
  empresaId: null,
  leaseId: null,
  indiceAsiento: null,
};

// Helpers
function $(id) { return document.getElementById(id); }

function mostrarResultado(id, texto, ok = true) {
  const el = $(id);
  el.textContent = texto;
  el.className = "resultado " + (ok ? "ok" : "error");
}

async function api(method, path, body = null, params = null) {
  let url = path;
  if (params) {
    const qs = new URLSearchParams(params).toString();
    url += "?" + qs;
  }
  const opts = { method, headers: { "Content-Type": "application/json" } };
  if (body) opts.body = JSON.stringify(body);
  const r = await fetch(url, opts);
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.detail || `HTTP ${r.status}`);
  return data;
}

// Paso 1: crear obra
async function crearObra() {
  try {
    estado.obraId = $("obra-id").value;
    estado.empresaId = $("empresa-id").value;
    const d = await api("POST", "/obras", {
      obra_id: estado.obraId,
      empresa_id: estado.empresaId,
      nombre: $("obra-nombre").value,
      cliente_nif: $("obra-cliente").value,
    });
    mostrarResultado("res-obra", `✓ Obra ${d.obra_id} creada`);
  } catch (e) {
    mostrarResultado("res-obra", `✗ ${e.message}`, false);
  }
}

// Paso 2: pedir lease
async function pedirLease() {
  try {
    if (!estado.empresaId) throw new Error("Primero crea la obra");
    const d = await api("POST", "/leases", {
      empresa_id: estado.empresaId,
      obra_id: estado.obraId,
      tipo: "asiento",
      operario: $("lease-operario").value,
      duracion_min: parseInt($("lease-duracion").value),
    });
    estado.leaseId = d.lease_id;
    mostrarResultado("res-lease",
      `✓ Lease ${d.lease_id.slice(0,8)}...\n` +
      `  Índice reservado: ${d.indice_reservado}\n` +
      `  Expira: ${d.expira_en}`
    );
  } catch (e) {
    mostrarResultado("res-lease", `✗ ${e.message}`, false);
  }
}

// Paso 3: crear asiento
async function crearAsiento() {
  try {
    if (!estado.leaseId) throw new Error("Primero pide un lease");
    const codigo = $("asiento-codigo").value;
    // Parámetros según el código de acto
    let parametros = {};
    if (codigo === "A_FACT_EMIT_SERV_NAC_SIN_RET") {
      parametros = { base_centimos: 4615000, iva_pct: 21, cliente_nif: "MFOM" };
    } else if (codigo === "A_COBRO_CLIENTE_TRANSF") {
      parametros = { importe_centimos: 5584150, cliente_nif: "MFOM" };
    } else if (codigo === "A_NOMINA_MENSUAL") {
      parametros = {
        bruto_centimos: 200000, irpf_pct: 15,
        ss_trabajador_pct: 6.35, ss_empresa_pct: 30,
        trabajador_nif: "12345678Z",
      };
    } else if (codigo === "A_FACT_REC_GASTO_NAC") {
      parametros = {
        base_centimos: 100000, iva_pct: 21,
        cuenta_gasto: "629", proveedor_nif: "B12345678",
      };
    }
    const d = await api("POST", "/asientos", {
      empresa_id: estado.empresaId,
      codigo_acto: codigo,
      fecha: $("asiento-fecha").value,
      concepto: $("asiento-concepto").value,
      creado_por: $("asiento-creado-por").value,
      lease_id: estado.leaseId,
      obra_id: estado.obraId,
      parametros,
    });
    estado.indiceAsiento = d.indice;
    const lineas = d.lineas.map(l =>
      (l.debe_centimos > 0 ? "  D " : "  H ") +
      l.cuenta_pgc.padStart(6) + "  " +
      ((l.debe_centimos || l.haber_centimos) / 100).toFixed(2).padStart(12)
    ).join("\n");
    mostrarResultado("res-asiento",
      `✓ Asiento #${d.indice} (BORRADOR)\n` + lineas + `\n  Hash: ${d.hash.slice(0,16)}...`
    );
  } catch (e) {
    mostrarResultado("res-asiento", `✗ ${e.message}`, false);
  }
}

// Paso 4: visar
async function visar() {
  try {
    if (estado.indiceAsiento === null) throw new Error("Primero crea un asiento");
    const d = await api("POST",
      `/asientos/${estado.indiceAsiento}/visar`,
      { operario_visador: $("visar-operario").value },
      { empresa_id: estado.empresaId }
    );
    mostrarResultado("res-visar", `✓ Estado: ${d.estado}`);
  } catch (e) {
    mostrarResultado("res-visar", `✗ ${e.message}`, false);
  }
}

// Paso 5: aprobar
async function aprobar() {
  try {
    if (estado.indiceAsiento === null) throw new Error("Primero visa el asiento");
    const d = await api("POST",
      `/asientos/${estado.indiceAsiento}/aprobar`,
      { operario_aprobador: $("aprobar-operario").value },
      { empresa_id: estado.empresaId }
    );
    mostrarResultado("res-aprobar", `✓ Estado: ${d.estado}`);
  } catch (e) {
    mostrarResultado("res-aprobar", `✗ ${e.message}`, false);
  }
}

// Paso 6: rizomizar
async function rizomizar() {
  try {
    if (estado.indiceAsiento === null) throw new Error("Primero aprueba el asiento");
    const ok = $("rizomizar-ok").checked;
    const d = await api("POST",
      `/asientos/${estado.indiceAsiento}/rizomizar`,
      { ok, alerta: ok ? null : $("rizomizar-alerta").value },
      { empresa_id: estado.empresaId }
    );
    mostrarResultado("res-rizomizar", `✓ Estado: ${d.estado}`);
  } catch (e) {
    mostrarResultado("res-rizomizar", `✗ ${e.message}`, false);
  }
}

// Ver estado final
async function verEstado() {
  try {
    if (!estado.empresaId) throw new Error("Primero crea la obra");
    const asientos = await api("GET", "/asientos",
      null, { empresa_id: estado.empresaId, estado: "RIZOMIZADO" });
    const verif = await api("POST", "/verificar",
      { empresa_id: estado.empresaId });
    const lista = asientos.map(a =>
      `  #${a.indice}  ${a.fecha}  ${a.concepto}`
    ).join("\n");
    mostrarResultado("res-estado",
      `Asientos RIZOMIZADOS: ${asientos.length}\n${lista}\n\n` +
      `Cadena: ${verif.cadena_valida ? "✓ VÁLIDA" : "✗ ROTA"} (${verif.total} asientos)`
    );
  } catch (e) {
    mostrarResultado("res-estado", `✗ ${e.message}`, false);
  }
}
