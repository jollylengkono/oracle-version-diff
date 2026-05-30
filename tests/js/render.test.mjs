import { test } from 'node:test';
import assert from 'node:assert/strict';
import { escapeHtml, renderItem, renderItems, renderSideBySide } from '../../js/render.js';

test('escapeHtml neutralizes angle brackets and ampersands', () => {
  assert.equal(escapeHtml('<a>&"'), '&lt;a&gt;&amp;&quot;');
});

test('renderItem includes title, description, and source link', () => {
  const html = renderItem({ title: 'Feature X', description: 'does things', source_url: 'https://docs.oracle.com/x' });
  assert.match(html, /Feature X/);
  assert.match(html, /does things/);
  assert.match(html, /href="https:\/\/docs\.oracle\.com\/x"/);
});

test('renderItems lists every item in a section', () => {
  const record = { sections: { whats_new: [
    { title: 'AlphaFeature', description: 'a', source_url: 'https://docs.oracle.com/a' },
    { title: 'BetaFeature', description: 'b', source_url: 'https://docs.oracle.com/b' }
  ] } };
  const html = renderItems(record, 'whats_new');
  assert.match(html, /AlphaFeature/);
  assert.match(html, /BetaFeature/);
});

test('renderItems shows an empty-state message when a section has no items', () => {
  const html = renderItems({ sections: { deprecated: [] } }, 'deprecated');
  assert.match(html, /No entries/);
});

test('renderSideBySide shows both version labels and their items in two columns', () => {
  const older = { version: '23.10', release_label: 'Release 23.10', sections: { whats_new: [
    { title: 'OldFeature', description: 'x', source_url: 'https://docs.oracle.com/o' } ] } };
  const newer = { version: '23.26.1.0.0', release_label: 'Release 26ai (23.26.1.0.0)', sections: { whats_new: [
    { title: 'NewFeature', description: 'y', source_url: 'https://docs.oracle.com/n' } ] } };
  const html = renderSideBySide('whats_new', older, newer);
  assert.match(html, /class="cols"/);
  assert.match(html, /Release 23\.10/);
  assert.match(html, /Release 26ai/);
  assert.match(html, /OldFeature/);
  assert.match(html, /NewFeature/);
});
