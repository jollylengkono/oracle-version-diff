import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const index = JSON.parse(readFileSync('data/index.json', 'utf8'));

test('index includes Oracle Database from 12c to latest 26ai with LTS metadata', () => {
  const product = index.products.find(p => p.id === 'oracle-database');

  assert.ok(product);
  assert.equal(product.label, 'Oracle Database');
  assert.deepEqual(product.versions.map(v => v.version), ['26ai', '21c', '19c', '12c']);
  assert.equal(product.versions[0].record_type, 'release');
  assert.deepEqual(
    product.versions.map(v => [v.version, v.is_lts]),
    [['26ai', true], ['21c', false], ['19c', true], ['12c', false]]
  );
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

test('index includes Oracle WebLogic Server from 11g to 15c with LTS metadata', () => {
  const product = index.products.find(p => p.id === 'oracle-weblogic-server');

  assert.ok(product);
  assert.equal(product.label, 'Oracle WebLogic Server');
  assert.deepEqual(product.versions.map(v => v.version), ['15c', '14c', '12c', '11g']);
  assert.deepEqual(product.versions.map(v => v.is_lts), [false, false, false, false]);
});

test('Oracle WebLogic Server 15c record has release delta sections', () => {
  const product = index.products.find(p => p.id === 'oracle-weblogic-server');
  const latest = product.versions.find(v => v.version === '15c');
  const record = JSON.parse(readFileSync(`data/${latest.file}`, 'utf8'));

  assert.equal(record.product, 'oracle-weblogic-server');
  assert.ok(record.sections.whats_new.length > 0);
  assert.ok(record.sections.behavior_changes.length > 0);
  assert.ok(record.sections.deprecated.length > 0);
});
