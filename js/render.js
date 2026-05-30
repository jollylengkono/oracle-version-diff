export function escapeHtml(s) {
  return String(s)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;');
}

export function renderItem(status, section, item) {
  const heading = section === 'certification'
    ? `${escapeHtml(item.category)}: ${escapeHtml(item.value)}`
    : escapeHtml(item.title);
  const desc = item.description ? `<p class="item__desc">${escapeHtml(item.description)}</p>` : '';
  return `<article class="item item--${status}">
  <h4 class="item__title">${heading}</h4>
  ${desc}
  <a class="item__source" href="${escapeHtml(item.source_url)}" target="_blank" rel="noopener">Official doc</a>
</article>`;
}

const GROUPS = [['added', 'Added'], ['changed', 'Changed'], ['removed', 'Removed']];

export function renderSection(section, diff) {
  const blocks = [];
  for (const [status, label] of GROUPS) {
    const items = diff[status];
    if (!items.length) continue;
    blocks.push(`<div class="group group--${status}">
  <h3 class="group__label">${label} <span class="group__count">${items.length}</span></h3>
  ${items.map(i => renderItem(status, section, i)).join('\n')}
</div>`);
  }
  if (!blocks.length) return `<p class="empty">No differences in this section.</p>`;
  return blocks.join('\n');
}
