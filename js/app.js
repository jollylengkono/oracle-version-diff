// js/app.js
import { diffRecords, SECTIONS } from './diff.js';
import { renderSection } from './render.js';
import { loadIndex, loadRecord } from './datasource.js';

const SECTION_LABELS = {
  certification: 'Certification',
  whats_new: "What's New",
  behavior_changes: 'Behavior Changes',
  deprecated: 'Deprecated',
  desupported: 'Desupported / Removed'
};

export function pickDefaultVersions(versions) {
  const sorted = [...versions].sort((a, b) => b.order - a.order);
  const newer = sorted[0];
  const older = sorted[1] || sorted[0];
  return [older, newer];
}

function fillSelect(select, versions, selectedVersion) {
  select.innerHTML = versions
    .map(v => `<option value="${v.version}" ${v.version === selectedVersion ? 'selected' : ''}>${v.label}</option>`)
    .join('');
}

function renderTabs(container, panels) {
  container.innerHTML = SECTIONS
    .map((s, i) => `<button class="tab ${i === 0 ? 'tab--active' : ''}" data-section="${s}">${SECTION_LABELS[s]}</button>`)
    .join('');
  container.addEventListener('click', (e) => {
    const btn = e.target.closest('.tab');
    if (!btn) return;
    container.querySelectorAll('.tab').forEach(t => t.classList.remove('tab--active'));
    btn.classList.add('tab--active');
    Object.entries(panels).forEach(([section, el]) => {
      el.hidden = section !== btn.dataset.section;
    });
  });
}

async function loadVersion(product, version) {
  const meta = product.versions.find(v => v.version === version);
  return loadRecord(meta.file);
}

function renderComparison(panelsHost, older, newer) {
  const diff = diffRecords(older, newer);
  panelsHost.innerHTML = '';
  const panels = {};
  SECTIONS.forEach((section, i) => {
    const panel = document.createElement('section');
    panel.className = 'panel';
    panel.hidden = i !== 0;
    panel.innerHTML = renderSection(section, diff[section]);
    panelsHost.appendChild(panel);
    panels[section] = panel;
  });
  return panels;
}

async function main() {
  const index = await loadIndex();
  const product = index.products[0]; // v1: GoldenGate only
  const olderSel = document.getElementById('older');
  const newerSel = document.getElementById('newer');
  const tabsHost = document.getElementById('tabs');
  const panelsHost = document.getElementById('panels');
  const updated = document.getElementById('updated');

  const [defOlder, defNewer] = pickDefaultVersions(product.versions);
  fillSelect(olderSel, product.versions, defOlder.version);
  fillSelect(newerSel, product.versions, defNewer.version);

  async function refresh() {
    const [older, newer] = await Promise.all([
      loadVersion(product, olderSel.value),
      loadVersion(product, newerSel.value)
    ]);
    const panels = renderComparison(panelsHost, older, newer);
    renderTabs(tabsHost, panels);
    updated.textContent = `Data last updated: ${newer.last_updated}`;
  }

  olderSel.addEventListener('change', refresh);
  newerSel.addEventListener('change', refresh);
  await refresh();
}

if (typeof document !== 'undefined') {
  main().catch(err => {
    const host = document.getElementById('panels');
    if (host) host.innerHTML = `<p class="error">${err.message}</p>`;
  });
}
