import { test } from 'node:test';
import assert from 'node:assert/strict';
import { productIconSvg } from '../../js/productIcons.js';

const PRODUCT_IDS = [
  'oracle-database',
  'oracle-weblogic-server',
  'oracle-goldengate'
];

test('productIconSvg returns original inline SVG for known products', () => {
  PRODUCT_IDS.forEach((productId) => {
    const svg = productIconSvg(productId);

    assert.match(svg, /<svg[^>]+viewBox="0 0 32 32"/);
    assert.match(svg, new RegExp(`data-product-icon="${productId}"`));
    assert.match(svg, /class="product-icon-svg product-icon-svg--/);
    assert.match(svg, /shape-rendering="crispEdges"/);
    assert.doesNotMatch(svg, /<image|href=|https?:\/\//);
  });
});

test('productIconSvg uses concrete product metaphors', () => {
  assert.match(productIconSvg('oracle-database'), /product-icon-svg--database/);
  assert.match(productIconSvg('oracle-weblogic-server'), /product-icon-svg--weblogic/);
  assert.match(productIconSvg('oracle-goldengate'), /product-icon-svg--goldengate/);
});

test('productIconSvg returns fallback SVG for unknown products', () => {
  const svg = productIconSvg('unknown-product');

  assert.match(svg, /data-product-icon="default"/);
  assert.match(svg, /product-icon-svg--default/);
  assert.match(svg, /<svg[^>]+viewBox="0 0 32 32"/);
});
