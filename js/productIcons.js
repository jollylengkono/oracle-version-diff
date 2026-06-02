const ICONS = {
  'oracle-database': `<svg class="product-icon-svg product-icon-svg--database" data-product-icon="oracle-database" viewBox="0 0 32 32" width="40" height="40" aria-hidden="true" focusable="false" shape-rendering="crispEdges">
  <rect width="32" height="32" fill="var(--product-icon-bg, #160f17)"/>
  <rect x="7" y="5" width="18" height="4" fill="var(--product-icon-accent, #e8001b)"/>
  <rect x="5" y="9" width="22" height="5" fill="var(--product-icon-ink, #f0e2e2)"/>
  <rect x="7" y="14" width="18" height="9" fill="var(--product-icon-muted, #7a4d5e)"/>
  <rect x="5" y="23" width="22" height="5" fill="var(--product-icon-accent, #e8001b)"/>
  <rect x="9" y="16" width="14" height="2" fill="var(--product-icon-bg, #160f17)" opacity=".45"/>
  <rect x="9" y="20" width="14" height="2" fill="var(--product-icon-bg, #160f17)" opacity=".45"/>
</svg>`,
  'oracle-weblogic-server': `<svg class="product-icon-svg product-icon-svg--weblogic" data-product-icon="oracle-weblogic-server" viewBox="0 0 32 32" width="40" height="40" aria-hidden="true" focusable="false" shape-rendering="crispEdges">
  <rect width="32" height="32" fill="var(--product-icon-bg, #160f17)"/>
  <rect x="6" y="5" width="20" height="6" fill="var(--product-icon-accent, #e8001b)"/>
  <rect x="6" y="13" width="20" height="6" fill="var(--product-icon-muted, #7a4d5e)"/>
  <rect x="6" y="21" width="20" height="6" fill="var(--product-icon-ink, #f0e2e2)"/>
  <rect x="9" y="7" width="3" height="2" fill="var(--product-icon-bg, #160f17)"/>
  <rect x="9" y="15" width="3" height="2" fill="var(--product-icon-bg, #160f17)"/>
  <rect x="9" y="23" width="3" height="2" fill="var(--product-icon-bg, #160f17)"/>
  <rect x="19" y="7" width="3" height="2" fill="var(--product-icon-ink, #f0e2e2)"/>
  <rect x="19" y="15" width="3" height="2" fill="var(--product-icon-accent, #e8001b)"/>
  <rect x="19" y="23" width="3" height="2" fill="var(--product-icon-accent, #e8001b)"/>
</svg>`,
  'oracle-goldengate': `<svg class="product-icon-svg product-icon-svg--goldengate" data-product-icon="oracle-goldengate" viewBox="0 0 32 32" width="40" height="40" aria-hidden="true" focusable="false" shape-rendering="crispEdges">
  <rect width="32" height="32" fill="var(--product-icon-bg, #160f17)"/>
  <rect x="4" y="12" width="8" height="8" fill="var(--product-icon-ink, #f0e2e2)"/>
  <rect x="20" y="12" width="8" height="8" fill="var(--product-icon-ink, #f0e2e2)"/>
  <rect x="11" y="14" width="10" height="4" fill="var(--product-icon-accent, #e8001b)"/>
  <rect x="14" y="9" width="4" height="14" fill="var(--product-icon-accent, #e8001b)"/>
  <rect x="7" y="15" width="2" height="2" fill="var(--product-icon-bg, #160f17)"/>
  <rect x="23" y="15" width="2" height="2" fill="var(--product-icon-bg, #160f17)"/>
  <rect x="14" y="14" width="4" height="4" fill="var(--product-icon-muted, #7a4d5e)"/>
</svg>`
};

const FALLBACK_ICON = `<svg class="product-icon-svg product-icon-svg--default" data-product-icon="default" viewBox="0 0 32 32" width="40" height="40" aria-hidden="true" focusable="false" shape-rendering="crispEdges">
  <rect width="32" height="32" fill="var(--product-icon-bg, #160f17)"/>
  <rect x="8" y="8" width="16" height="16" fill="var(--product-icon-accent, #e8001b)"/>
  <rect x="12" y="12" width="8" height="8" fill="var(--product-icon-ink, #f0e2e2)"/>
</svg>`;

export function productIconSvg(productId) {
  return Object.hasOwn(ICONS, productId) ? ICONS[productId] : FALLBACK_ICON;
}
