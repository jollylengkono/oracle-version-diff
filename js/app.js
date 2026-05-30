// js/app.js
import { aggregateRange } from './diff.js';
import { renderAggregated } from './render.js';
import { loadIndex, loadRecord } from './datasource.js';

// Sections shown in the UI. The rolling release notes populate these three;
// certification/desupported are reserved in the schema but not shown in v1.
const SECTIONS = ['whats_new', 'behavior_changes', 'deprecated'];

const SECTION_LABELS = {
  whats_new: "What's New",
  behavior_changes: 'Behavior Changes',
  deprecated: 'Deprecated & Desupported'
};

export function pickDefaultVersions(versions) {
  const sorted = [...versions].sort((a, b) => b.order - a.order);
  const newer = sorted.find(v => v.record_type === 'release') || sorted[0];
  const older = sorted.find(v => v.record_type === 'baseline') || sorted[1] || sorted[0];
  return [older, newer];
}

export function pickDefaultProduct(products) {
  return products.find(p => p.id === 'oracle-database') || products[0];
}

export function releaseDeltaHeading(current, target) {
  return `Release delta from ${current} to ${target}`;
}

export function releaseDeltaSubheading(current, target) {
  return `Changes introduced after ${current} through ${target}`;
}

function fillSelect(select, versions, selectedVersion) {
  select.innerHTML = versions
    .map(v => `<option value="${v.version}" ${v.version === selectedVersion ? 'selected' : ''}>${v.label}</option>`)
    .join('');
}

function fillProductSelect(select, products, selectedProductId) {
  select.innerHTML = products
    .map(p => `<option value="${p.id}" ${p.id === selectedProductId ? 'selected' : ''}>${p.label}</option>`)
    .join('');
}

function renderTabs(container, panels) {
  container.innerHTML = SECTIONS
    .map((s, i) => `<button class="tab ${i === 0 ? 'tab--active' : ''}" data-section="${s}">${SECTION_LABELS[s]}</button>`)
    .join('');
  container.onclick = (e) => {
    const btn = e.target.closest('.tab');
    if (!btn) return;
    container.querySelectorAll('.tab').forEach(t => t.classList.remove('tab--active'));
    btn.classList.add('tab--active');
    Object.entries(panels).forEach(([section, el]) => {
      el.hidden = section !== btn.dataset.section;
    });
  };
}

async function loadAllRecords(product) {
  return Promise.all(product.versions.map(meta => loadRecord(meta.file)));
}

function renderComparison(panelsHost, aggregated) {
  panelsHost.innerHTML = '';
  const panels = {};
  SECTIONS.forEach((section, i) => {
    const panel = document.createElement('section');
    panel.className = 'panel';
    panel.hidden = i !== 0;
    panel.innerHTML = renderAggregated(section, aggregated[section] || []);
    panelsHost.appendChild(panel);
    panels[section] = panel;
  });
  return panels;
}

async function main() {
  const index = await loadIndex();
  const productSel = document.getElementById('product');
  const olderSel = document.getElementById('older');
  const newerSel = document.getElementById('newer');
  const tabsHost = document.getElementById('tabs');
  const panelsHost = document.getElementById('panels');
  const updated = document.getElementById('updated');
  const deltaHeading = document.getElementById('delta-heading');
  const deltaSubheading = document.getElementById('delta-subheading');

  const defProduct = pickDefaultProduct(index.products);
  fillProductSelect(productSel, index.products, defProduct.id);
  let records = [];

  async function refresh() {
    const product = index.products.find(p => p.id === productSel.value) || index.products[0];
    const aggregated = aggregateRange(records, olderSel.value, newerSel.value);
    const panels = renderComparison(panelsHost, aggregated);
    renderTabs(tabsHost, panels);
    const selected = records.find(r => r.version === newerSel.value) || records[0];
    deltaHeading.textContent = releaseDeltaHeading(olderSel.value, newerSel.value);
    deltaSubheading.textContent = releaseDeltaSubheading(olderSel.value, newerSel.value);
    updated.textContent = `${product.label} data last updated: ${selected.last_updated}`;
  }

  async function loadProduct(product) {
    const [defOlder, defNewer] = pickDefaultVersions(product.versions);
    fillSelect(olderSel, product.versions, defOlder.version);
    fillSelect(newerSel, product.versions, defNewer.version);
    records = await loadAllRecords(product);
    await refresh();
  }

  productSel.addEventListener('change', async () => {
    const product = index.products.find(p => p.id === productSel.value) || index.products[0];
    await loadProduct(product);
  });
  olderSel.addEventListener('change', refresh);
  newerSel.addEventListener('change', refresh);
  await loadProduct(defProduct);
}

if (typeof document !== 'undefined') {
  main().catch(err => {
    const host = document.getElementById('panels');
    if (host) host.innerHTML = `<p class="error">${err.message}</p>`;
  });
}
