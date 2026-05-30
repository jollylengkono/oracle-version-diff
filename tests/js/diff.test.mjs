import { test } from 'node:test';
import assert from 'node:assert/strict';
import { keyFor, diffSection, diffRecords, SECTIONS } from '../../js/diff.js';
import { pickDefaultVersions } from '../../js/app.js';

test('keyFor uses title for feature sections', () => {
  assert.equal(keyFor('whats_new', { title: 'A', description: 'x' }), 'A');
});

test('keyFor uses category::value for certification', () => {
  assert.equal(keyFor('certification', { category: 'DB', value: 'v19' }), 'DB::v19');
});

test('diffSection classifies added, removed, changed, unchanged', () => {
  const older = [
    { title: 'keep', description: 'same' },
    { title: 'mod', description: 'old' },
    { title: 'gone', description: 'x' }
  ];
  const newer = [
    { title: 'keep', description: 'same' },
    { title: 'mod', description: 'new' },
    { title: 'fresh', description: 'y' }
  ];
  const r = diffSection('whats_new', older, newer);
  assert.deepEqual(r.added.map(i => i.title), ['fresh']);
  assert.deepEqual(r.removed.map(i => i.title), ['gone']);
  assert.deepEqual(r.changed.map(i => i.title), ['mod']);
  assert.deepEqual(r.unchanged.map(i => i.title), ['keep']);
});

test('diffRecords covers all five sections', () => {
  const empty = { certification: [], whats_new: [], behavior_changes: [], deprecated: [], desupported: [] };
  const older = { sections: { ...empty } };
  const newer = { sections: { ...empty, whats_new: [{ title: 'n', description: 'd' }] } };
  const r = diffRecords(older, newer);
  assert.deepEqual(SECTIONS, ['certification', 'whats_new', 'behavior_changes', 'deprecated', 'desupported']);
  assert.equal(r.whats_new.added.length, 1);
  assert.equal(r.certification.added.length, 0);
});

test('pickDefaultVersions returns [previous, latest] by order desc', () => {
  const versions = [
    { version: '21c', order: 1 },
    { version: '23ai', order: 2 },
    { version: '19c', order: 0 }
  ];
  const [older, newer] = pickDefaultVersions(versions);
  assert.equal(newer.version, '23ai');
  assert.equal(older.version, '21c');
});

test('pickDefaultVersions handles a single version', () => {
  const [older, newer] = pickDefaultVersions([{ version: '23ai', order: 2 }]);
  assert.equal(older.version, '23ai');
  assert.equal(newer.version, '23ai');
});
