import { test } from 'node:test';
import assert from 'node:assert/strict';
import { escapeHtml, renderItem, renderSection } from '../../js/render.js';

test('escapeHtml neutralizes angle brackets and ampersands', () => {
  assert.equal(escapeHtml('<a>&"'), '&lt;a&gt;&amp;&quot;');
});

test('renderItem includes status class, title, description, and source link', () => {
  const html = renderItem('added', 'certification',
    { category: 'DB', value: 'v23', source_url: 'https://docs.oracle.com/x' });
  assert.match(html, /item--added/);
  assert.match(html, /DB/);
  assert.match(html, /href="https:\/\/docs\.oracle\.com\/x"/);
});

test('renderSection emits added, changed and removed groups and skips empty groups', () => {
  const diff = {
    added: [{ title: 'A', description: 'd', source_url: 'https://docs.oracle.com/a' }],
    changed: [],
    removed: [{ title: 'R', description: 'd', source_url: 'https://docs.oracle.com/r' }],
    unchanged: []
  };
  const html = renderSection('whats_new', diff);
  assert.match(html, /item--added/);
  assert.match(html, /item--removed/);
  assert.doesNotMatch(html, /item--changed/);
});

test('renderSection shows an empty-state message when nothing differs', () => {
  const html = renderSection('deprecated', { added: [], changed: [], removed: [], unchanged: [] });
  assert.match(html, /No differences/);
});
