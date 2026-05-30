import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const index = JSON.parse(readFileSync('data/index.json', 'utf8'));

test('index includes Oracle Database from 19c to latest 26ai', () => {
  const product = index.products.find(p => p.id === 'oracle-database');

  assert.ok(product);
  assert.equal(product.label, 'Oracle Database');
  assert.deepEqual(product.versions.map(v => v.version), ['26ai', '19c']);
  assert.equal(product.versions[0].record_type, 'release');
  assert.equal(product.versions[1].record_type, 'baseline');
});

test('Oracle Database 26ai record has release delta sections', () => {
  const product = index.products.find(p => p.id === 'oracle-database');
  const latest = product.versions.find(v => v.version === '26ai');
  const record = JSON.parse(readFileSync(`data/${latest.file}`, 'utf8'));

  assert.equal(record.product, 'oracle-database');
  assert.ok(record.sections.whats_new.length > 0);
  assert.ok(record.sections.behavior_changes.length > 0);
  assert.ok(record.sections.deprecated.length > 0);
});
