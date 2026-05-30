import { test } from 'node:test';
import assert from 'node:assert/strict';
import { escapeHtml, renderItem, renderItems, renderSideBySide, renderAggregated } from '../../js/render.js';

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

test('renderAggregated shows one list with release version labels', () => {
  const html = renderAggregated('whats_new', [
    {
      title: 'RangeFeature',
      description: 'introduced in range',
      source_url: 'https://docs.oracle.com/r',
      introduced_label: 'Release 23.5',
      introduced_version: '23.5'
    }
  ]);

  assert.doesNotMatch(html, /class="cols"/);
  assert.match(html, /RangeFeature/);
  assert.match(html, />23\.5</);
});

test('renderAggregated marks release versions for card styling', () => {
  const html = renderAggregated('whats_new', [
    {
      title: 'ConsoleFeature',
      description: 'visible in console',
      source_url: 'https://docs.oracle.com/c',
      introduced_label: 'Release 23.6',
      introduced_version: '23.6'
    }
  ]);

  assert.match(html, /class="item__version"/);
  assert.match(html, />23\.6</);
  assert.doesNotMatch(html, /Release 23\.6/);
});

test('renderItem marks source links as documentation buttons', () => {
  const html = renderItem({
    title: 'DocsFeature',
    description: 'links to docs',
    source_url: 'https://docs.oracle.com/docs-feature'
  });

  assert.match(html, /class="item__source"/);
  assert.match(html, />Official doc</);
});
