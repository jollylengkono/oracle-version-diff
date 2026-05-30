export function escapeHtml(s) {
  return String(s)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;');
}

export function renderItem(item) {
  const desc = item.description ? `<p class="item__desc">${escapeHtml(item.description)}</p>` : '';
  const versionLabel = item.introduced_version || item.introduced_label;
  const version = versionLabel
    ? `<span class="item__version">${escapeHtml(versionLabel)}</span>`
    : '';
  const link = item.source_url
    ? `<a class="item__source" href="${escapeHtml(item.source_url)}" target="_blank" rel="noopener">Official doc</a>`
    : '';
  return `<article class="item">
  <div class="item__head">
    <h4 class="item__title">${escapeHtml(item.title)}</h4>
    ${version}
  </div>
  ${desc}
  ${link}
</article>`;
}

export function renderItems(record, section) {
  const items = (record.sections && record.sections[section]) || [];
  if (!items.length) return `<p class="empty">No entries for this release.</p>`;
  return items.map(renderItem).join('\n');
}

// Two columns for one section: the two selected version records side by side.
export function renderSideBySide(section, older, newer) {
  return `<div class="cols">
  <div class="col">
    <h3 class="col__head">${escapeHtml(older.release_label || older.version)}</h3>
    ${renderItems(older, section)}
  </div>
  <div class="col">
    <h3 class="col__head">${escapeHtml(newer.release_label || newer.version)}</h3>
    ${renderItems(newer, section)}
  </div>
</div>`;
}

export function renderAggregated(section, items) {
  if (!items.length) return `<p class="empty">No entries in this upgrade range.</p>`;
  return `<div class="range-list">
  ${items.map(renderItem).join('\n')}
</div>`;
}
