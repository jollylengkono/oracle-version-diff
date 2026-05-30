import { test } from 'node:test';
import assert from 'node:assert/strict';
import { keyFor, diffSection, diffRecords, aggregateRange, SECTIONS } from '../../js/diff.js';
import { pickDefaultProduct, pickDefaultVersions, releaseDeltaHeading, releaseDeltaSubheading } from '../../js/app.js';

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

test('pickDefaultVersions chooses latest baseline as older and latest release as newer', () => {
  const versions = [
    { version: '23.26.2.0.0', order: 18, record_type: 'release' },
    { version: '23.26.1.0.0', order: 17, record_type: 'release' },
    { version: '21c', order: 2, record_type: 'baseline' },
    { version: '19c', order: 1, record_type: 'baseline' }
  ];

  const [older, newer] = pickDefaultVersions(versions);

  assert.equal(older.version, '21c');
  assert.equal(newer.version, '23.26.2.0.0');
});

test('pickDefaultProduct prefers Oracle Database when available', () => {
  const products = [
    { id: 'oracle-goldengate', label: 'Oracle GoldenGate' },
    { id: 'oracle-database', label: 'Oracle Database' }
  ];

  assert.equal(pickDefaultProduct(products).id, 'oracle-database');
});

test('release delta copy describes directional current-to-target flow', () => {
  assert.equal(releaseDeltaHeading('19c', '26ai'), 'Release delta from 19c to 26ai');
  assert.equal(
    releaseDeltaSubheading('19c', '26ai'),
    'Changes introduced after 19c through 26ai'
  );
});

test('aggregateRange concatenates releases after older through newer and badges source release', () => {
  const records = [
    {
      version: '23.4',
      release_label: 'Release 23.4',
      released: '2024-05-01',
      sections: { whats_new: [{ title: 'base', description: 'b' }], behavior_changes: [], deprecated: [] }
    },
    {
      version: '23.5',
      release_label: 'Release 23.5',
      released: '2024-07-01',
      sections: { whats_new: [{ title: 'mid', description: 'm' }], behavior_changes: [], deprecated: [] }
    },
    {
      version: '23.6',
      release_label: 'Release 23.6',
      released: '2024-10-01',
      sections: { whats_new: [{ title: 'new', description: 'n' }], behavior_changes: [], deprecated: [] }
    }
  ];

  const result = aggregateRange(records, '23.4', '23.6');
  assert.deepEqual(result.whats_new.map(i => i.title), ['mid', 'new']);
  assert.deepEqual(result.whats_new.map(i => i.introduced_version), ['23.5', '23.6']);
});

test('aggregateRange handles reversed and same-version selections', () => {
  const records = [
    { version: 'a', release_label: 'A', released: '2024-01-01', sections: { whats_new: [{ title: 'A' }], behavior_changes: [], deprecated: [] } },
    { version: 'b', release_label: 'B', released: '2024-02-01', sections: { whats_new: [{ title: 'B' }], behavior_changes: [], deprecated: [] } }
  ];

  assert.deepEqual(aggregateRange(records, 'b', 'a').whats_new.map(i => i.title), ['B']);
  assert.deepEqual(aggregateRange(records, 'b', 'b').whats_new.map(i => i.title), ['B']);
});

test('aggregateRange includes newer adjacent release when selected releases share a month', () => {
  const records = [
    { version: 'newer', release_label: 'Newer', released: '2026-01-01', sections: { whats_new: [{ title: 'newer item' }], behavior_changes: [], deprecated: [] } },
    { version: 'older', release_label: 'Older', released: '2026-01-01', sections: { whats_new: [{ title: 'older item' }], behavior_changes: [], deprecated: [] } }
  ];

  assert.deepEqual(aggregateRange(records, 'older', 'newer').whats_new.map(i => i.title), ['newer item']);
});

test('aggregateRange de-duplicates exact repeated section items', () => {
  const repeated = { title: 'same', description: 'same text', source_url: 'https://docs.oracle.com/same' };
  const records = [
    { version: 'newer', release_label: 'Newer', released: '2024-03-01', sections: { whats_new: [repeated], behavior_changes: [], deprecated: [] } },
    { version: 'middle', release_label: 'Middle', released: '2024-02-01', sections: { whats_new: [repeated], behavior_changes: [], deprecated: [] } },
    { version: 'older', release_label: 'Older', released: '2024-01-01', sections: { whats_new: [], behavior_changes: [], deprecated: [] } }
  ];

  assert.equal(aggregateRange(records, 'older', 'newer').whats_new.length, 1);
});

test('aggregateRange includes release items between baseline and modern release', () => {
  const records = [
    { version: '23.6', release_label: 'Release 23.6', record_type: 'release', released: '2024-10-01', sections: { whats_new: [{ title: '23.6 item' }], behavior_changes: [], deprecated: [] } },
    { version: '23.5', release_label: 'Release 23.5', record_type: 'release', released: '2024-07-01', sections: { whats_new: [{ title: '23.5 item' }], behavior_changes: [], deprecated: [] } },
    { version: '21c', release_label: 'Oracle GoldenGate 21c', record_type: 'baseline', released: '2021-01-01', sections: { whats_new: [], behavior_changes: [], deprecated: [] } },
    { version: '19c', release_label: 'Oracle GoldenGate 19c', record_type: 'baseline', released: '2019-01-01', sections: { whats_new: [], behavior_changes: [], deprecated: [] } }
  ];

  assert.deepEqual(aggregateRange(records, '19c', '23.6').whats_new.map(i => i.title), ['23.5 item', '23.6 item']);
});

test('aggregateRange includes the newer baseline when comparing 19c to 21c', () => {
  const records = [
    {
      version: '21c',
      release_label: 'Oracle GoldenGate 21c',
      record_type: 'baseline',
      released: '2021-01-01',
      sections: {
        whats_new: [{ title: '21c baseline item', source_url: 'https://docs.oracle.com/21c' }],
        behavior_changes: [],
        deprecated: []
      }
    },
    {
      version: '19c',
      release_label: 'Oracle GoldenGate 19c',
      record_type: 'baseline',
      released: '2019-01-01',
      sections: { whats_new: [], behavior_changes: [], deprecated: [] }
    }
  ];

  const result = aggregateRange(records, '19c', '21c');

  assert.deepEqual(result.whats_new.map(i => i.title), ['21c baseline item']);
  assert.deepEqual(result.whats_new.map(i => i.introduced_version), ['21c']);
});
