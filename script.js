/**
 * script.js — RECESA Dashboard de Vendedores
 * Lee datos desde datos.json (generado por actualizar.py)
 */

const COLORS = {
  Allan:   { line: '#E85C1A', fill: 'rgba(232,92,26,0.08)',  avatar: '#FDE8DC', text: '#C04A10' },
  Fabiola: { line: '#2D6B2D', fill: 'rgba(45,107,45,0.08)', avatar: '#E8F0E8', text: '#1A4A1A' },
};

const CAT_COLORS_ALLAN   = ['#E85C1A','#F28C60','#C04A10','#FAB894','#888','#aaa'];
const CAT_COLORS_FABIOLA = ['#2D6B2D','#4A9E4A','#1A4A1A','#7DC47D','#aaa','#ccc'];

let barChart, lineChart;

function fmtK(v) {
  return 'Q' + (v >= 1000000
    ? (v / 1000000).toFixed(1) + 'M'
    : v >= 1000 ? Math.round(v / 1000) + 'k' : v);
}

function fmtQ(v) {
  return 'Q' + Number(v).toLocaleString('es-GT', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

// ── Render KPIs ───────────────────────────────────────────
function renderKPIs(d) {
  document.getElementById('kpi-total').textContent =
    'Q' + (d.grandTotal / 1000000).toFixed(2) + 'M';
  document.getElementById('kpi-units').textContent =
    Number(d.grandUnits).toLocaleString('es-GT');
  document.getElementById('kpi-best').textContent = d.bestMonth;
  document.getElementById('kpi-best-sub').textContent = fmtQ(d.bestTotal);
  document.getElementById('kpi-price').textContent = fmtQ(d.avgPrice);
  document.getElementById('kpi-period').textContent = d.periodLabel;
}

// ── Render vendor cards ───────────────────────────────────
function renderVendorCards(d) {
  const container = document.getElementById('vendorCards');
  container.innerHTML = '';

  d.vendedores.forEach(v => {
    const s = d.vendedorSummary[v];
    const c = COLORS[v] || { line: '#888', fill: '#eee', avatar: '#eee', text: '#333' };
    const initials = v.substring(0, 2).toUpperCase();

    container.innerHTML += `
      <div class="vc">
        <div class="vc-header">
          <div class="vc-avatar" style="background:${c.avatar};color:${c.text};">${initials}</div>
          <div>
            <div class="vc-name">${v}</div>
            <div class="vc-role">Vendedor RECESA</div>
          </div>
        </div>
        <div class="vc-stat"><span>Ventas totales</span><strong>${fmtQ(s.total)}</strong></div>
        <div class="vc-stat"><span>Unidades</span><strong>${Number(s.units).toLocaleString('es-GT')}</strong></div>
        <div class="vc-stat"><span>Precio promedio</span><strong>${fmtQ(s.avgPrice)}</strong></div>
        <div class="vc-stat"><span>Categoría top</span><strong>${s.topCategory}</strong></div>
        <span class="vc-badge" style="background:${c.avatar};color:${c.text};">${s.pct}% del total</span>
      </div>
    `;
  });
}

// ── Charts ────────────────────────────────────────────────
function renderBarChart(d) {
  const datasets = d.vendedores.map(v => ({
    label: v,
    data: d.vendedorSeries[v] || [],
    backgroundColor: (COLORS[v] || {}).line || '#888',
    borderRadius: 2,
  }));

  if (barChart) barChart.destroy();
  barChart = new Chart(document.getElementById('barChart'), {
    type: 'bar',
    data: { labels: d.labels, datasets },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { stacked: true, ticks: { font: { size: 9 }, maxRotation: 45, autoSkip: false }, grid: { display: false } },
        y: { stacked: true, ticks: { font: { size: 9 }, callback: fmtK }, grid: { color: 'rgba(128,128,128,0.1)' } },
      },
    },
  });
}

function renderLineChart(d) {
  const datasets = d.vendedores.map(v => {
    const c = COLORS[v] || { line: '#888', fill: 'rgba(128,128,128,0.08)' };
    return {
      label: v,
      data: d.vendedorSeries[v] || [],
      borderColor: c.line,
      backgroundColor: c.fill,
      borderWidth: 2,
      pointRadius: 2.5,
      pointBackgroundColor: c.line,
      fill: true,
      tension: 0.35,
    };
  });

  if (lineChart) lineChart.destroy();
  lineChart = new Chart(document.getElementById('lineChart'), {
    type: 'line',
    data: { labels: d.labels, datasets },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { font: { size: 9 }, maxRotation: 45, autoSkip: false }, grid: { display: false } },
        y: { ticks: { font: { size: 9 }, callback: fmtK }, grid: { color: 'rgba(128,128,128,0.1)' } },
      },
    },
  });
}

// ── Categories ────────────────────────────────────────────
function renderCategories(cats, containerId, colors) {
  const container = document.getElementById(containerId);
  container.innerHTML = '';
  if (!cats || !cats.length) return;
  const maxVal = cats[0].total;
  cats.forEach((cat, i) => {
    const pct = Math.round((cat.total / maxVal) * 100);
    const color = colors[i] || '#aaa';
    container.innerHTML += `
      <div class="cat-item">
        <div class="cat-dot" style="background:${color}"></div>
        <div class="cat-name">${cat.name}</div>
        <div class="cat-bar-wrap"><div class="cat-bar" style="width:${pct}%;background:${color}"></div></div>
        <div class="cat-val">Q${Math.round(cat.total / 1000)}k</div>
      </div>`;
  });
}

// ── Top products ──────────────────────────────────────────
function renderTopProducts(products) {
  const container = document.getElementById('topProds');
  container.innerHTML = '';
  if (!products || !products.length) return;
  const maxVal = products[0].val;
  products.forEach((p, i) => {
    const pct = Math.round((p.val / maxVal) * 100);
    container.innerHTML += `
      <div class="prod-item">
        <div class="prod-rank">#${i + 1}</div>
        <div class="prod-name">${p.name}</div>
        <div class="prod-bar-wrap"><div class="prod-bar" style="width:${pct}%"></div></div>
        <div class="prod-val">Q${Math.round(p.val / 1000)}k</div>
      </div>`;
  });
}

// ── Render legend ─────────────────────────────────────────
function renderLegends(vendedores) {
  ['legend-bar', 'legend-line'].forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    el.innerHTML = '';
    vendedores.forEach(v => {
      const c = (COLORS[v] || {}).line || '#888';
      el.innerHTML += `
        <span class="leg">
          <span class="leg-sq" style="background:${c}"></span>${v}
        </span>`;
    });
  });
}

// ── Init ──────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  fetch('datos.json?v=' + Date.now())
    .then(res => {
      if (!res.ok) throw new Error('No se pudo cargar datos.json');
      return res.json();
    })
    .then(d => {
      renderKPIs(d);
      renderVendorCards(d);
      renderLegends(d.vendedores);
      renderBarChart(d);
      renderLineChart(d);

      d.vendedores.forEach((v, i) => {
        const cats = d.vendedorCategories[v] || [];
        const colors = i === 0 ? CAT_COLORS_ALLAN : CAT_COLORS_FABIOLA;
        renderCategories(cats, `cat${v}`, colors);
      });

      renderTopProducts(d.products);
    })
    .catch(err => {
      console.error(err);
      document.body.innerHTML += `
        <div style="padding:20px;color:red;font-family:sans-serif;">
          Error al cargar datos.json — corre primero: <code>python3 actualizar.py</code>
        </div>`;
    });
});
