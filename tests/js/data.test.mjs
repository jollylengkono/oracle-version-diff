import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const index = JSON.parse(readFileSync('data/index.json', 'utf8'));

test('index includes Oracle Database from 12c to latest 26ai with source-backed support metadata', () => {
  const product = index.products.find(p => p.id === 'oracle-database');

  assert.ok(product);
  assert.equal(product.label, 'Oracle Database');
  assert.deepEqual(product.versions.map(v => v.version), ['26ai', '21c', '19c', '12c']);
  assert.equal(product.versions[0].record_type, 'release');
  assert.deepEqual(
    product.versions.map(v => [v.version, v.support_track || null]),
    [
      ['26ai', 'Long Term Support Release'],
      ['21c', 'Innovation Release'],
      ['19c', 'Long Term Support Release'],
      ['12c', null]
    ]
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

test('Oracle Database curated records contain enough high-signal release data', () => {
  const product = index.products.find(p => p.id === 'oracle-database');
  const totals = product.versions
    .map(v => JSON.parse(readFileSync(`data/${v.file}`, 'utf8')))
    .reduce((acc, record) => {
      acc.whats_new += record.sections.whats_new.length;
      acc.behavior_changes += record.sections.behavior_changes.length;
      acc.deprecated += record.sections.deprecated.length;
      return acc;
    }, { whats_new: 0, behavior_changes: 0, deprecated: 0 });

  assert.ok(totals.whats_new >= 18);
  assert.ok(totals.behavior_changes >= 10);
  assert.ok(totals.deprecated >= 14);
});

test('index includes Oracle WebLogic Server from 11g to 15c without guessed LTS metadata', () => {
  const product = index.products.find(p => p.id === 'oracle-weblogic-server');

  assert.ok(product);
  assert.equal(product.label, 'Oracle WebLogic Server');
  assert.deepEqual(product.versions.map(v => v.version), ['15c', '14c', '12c', '11g']);
  assert.deepEqual(product.versions.map(v => 'support_track' in v), [false, false, false, false]);
  assert.deepEqual(product.versions.map(v => 'is_lts' in v), [false, false, false, false]);
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

test('Oracle WebLogic Server curated records contain enough high-signal release data', () => {
  const product = index.products.find(p => p.id === 'oracle-weblogic-server');
  const totals = product.versions
    .map(v => JSON.parse(readFileSync(`data/${v.file}`, 'utf8')))
    .reduce((acc, record) => {
      acc.whats_new += record.sections.whats_new.length;
      acc.behavior_changes += record.sections.behavior_changes.length;
      acc.deprecated += record.sections.deprecated.length;
      return acc;
    }, { whats_new: 0, behavior_changes: 0, deprecated: 0 });

  assert.ok(totals.whats_new >= 14);
  assert.ok(totals.behavior_changes >= 8);
  assert.ok(totals.deprecated >= 10);
});
