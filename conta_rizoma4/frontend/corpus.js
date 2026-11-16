const fmtEUR = (c) => {
  if (c === null || c === undefined) return '—';
  const s = c < 0 ? '-' : '';
  const a = Math.abs(c);
  return `${s}${(a / 100).toLocaleString('es-ES', {minimumFractionDigits: 2, maximumFractionDigits: 2})} €`;
};

async function api(path, params = null) {
  let url = path;
  if (params) {
    const qs = new URLSearchParams(params).toString();
    url += '?' + qs;
  }
  const r = await fetch(url);
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.detail || `HTTP ${r.status}`);
  return data;
}

async function cargarAgregado() {
  try {
    const d = await api('/corpus/agregado');
    const div = document.getElementById('totales');
    div.innerHTML = `
      <div class="total-card">
        <h3>Expedientes</h3>
        <div class="valor">${d.totales.n_expedientes}</div>
      </div>
      <div class="total-card">
        <h3>Sujetos</h3>
        <div class="valor">${d.totales.n_sujetos}</div>
      </div>
      <div class="total-card">
        <h3>Principal</h3>
        <div class="valor">${fmtEUR(parseInt(d.totales.principal))}</div>
      </div>
      <div class="total-card">
        <h3>Interés renunciado</h3>
        <div class="valor">${fmtEUR(parseInt(d.totales.interes_renunciado))}</div>
      </div>
      <div class="total-card">
        <h3>Interés compuesto</h3>
        <div class="valor">${fmtEUR(parseInt(d.totales.interes_compuesto))}</div>
      </div>
      <div class="total-card">
        <h3>Daño total</h3>
        <div class="valor">${fmtEUR(parseInt(d.totales.dano_total))}</div>
      </div>
    `;
  } catch (e) {
    alert('Error: ' + e.message);
  }
}

async function cargarExpedientes() {
  try {
    const universo = document.getElementById('filtro-universo').value;
    const params = universo ? { universo } : null;
    const data = await api('/corpus/expedientes', params);
    const div = document.getElementById('expedientes');
    if (data.length === 0) {
      div.innerHTML = '<p>(sin expedientes)</p>';
      return;
    }
    let html = '<table><thead><tr>' +
      '<th>ID</th><th>Sujeto</th><th>Universo</th>' +
      '<th>Vía</th><th>Concurso</th><th>Menoscabo</th>' +
      '</tr></thead><tbody>';
    for (const e of data) {
      html += `<tr class="universo-${e.universo}">
        <td>${e.expediente_id}</td>
        <td>${e.sujeto_id}</td>
        <td><strong>${e.universo}</strong></td>
        <td>${e.via_u1 || '—'}</td>
        <td>${e.estado_concurso}</td>
        <td>${e.porcentaje_menoscabo ? e.porcentaje_menoscabo.toFixed(0) + '%' : '—'}</td>
      </tr>`;
    }
    html += '</tbody></table>';
    div.innerHTML = html;
  } catch (e) {
    alert('Error: ' + e.message);
  }
}

async function cargarPatrones() {
  try {
    const d = await api('/corpus/patrones');
    const div = document.getElementById('patrones');
    let html = '';

    // Alertas
    if (d.alertas && d.alertas.length > 0) {
      html += '<h3>Alertas</h3>';
      for (const a of d.alertas) {
        html += `<div class="alerta">${a}</div>`;
      }
    } else {
      html += '<p>(sin alertas)</p>';
    }

    // Tasa de U1 por sector
    if (d.tasa_u1_por_sector && d.tasa_u1_por_sector.length > 0) {
      html += '<h3>Tasa de U1 por sector</h3>';
      html += '<table><thead><tr><th>Sector</th><th>Total</th><th>U1</th><th>Tasa</th></tr></thead><tbody>';
      for (const s of d.tasa_u1_por_sector) {
        html += `<tr><td>${s.sector}</td><td>${s.total}</td><td>${s.u1}</td><td>${s.tasa_u1}%</td></tr>`;
      }
      html += '</tbody></table>';
    }

    // Sección sexta
    if (d.tasa_seccion_sexta) {
      html += `<p><strong>Sección sexta:</strong> ${d.tasa_seccion_sexta.con_seccion} de ${d.tasa_seccion_sexta.total} (${d.tasa_seccion_sexta.tasa}%)</p>`;
    }

    // No diligencia
    if (d.tasa_no_diligencia) {
      html += `<p><strong>No diligencia:</strong> ${d.tasa_no_diligencia.no_diligente} de ${d.tasa_no_diligencia.total} (${d.tasa_no_diligencia.tasa}%)</p>`;
    }

    // Top daño
    if (d.top_dano && d.top_dano.length > 0) {
      html += '<h3>Top 10 daño</h3>';
      html += '<table><thead><tr><th>Expediente</th><th>Sujeto</th><th>Daño</th></tr></thead><tbody>';
      for (const t of d.top_dano) {
        html += `<tr><td>${t.expediente_id}</td><td>${t.nombre}</td><td>${fmtEUR(t.dano_total_centimos)}</td></tr>`;
      }
      html += '</tbody></table>';
    }

    div.innerHTML = html;
  } catch (e) {
    alert('Error: ' + e.message);
  }
}

// Cargar al inicio
cargarAgregado();
cargarExpedientes();
cargarPatrones();
