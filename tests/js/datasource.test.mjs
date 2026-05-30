import { test } from 'node:test';
import assert from 'node:assert/strict';
import { indexPath, recordPath } from '../../js/datasource.js';

test('indexPath points at the index under the data base', () => {
  assert.equal(indexPath(), 'data/index.json');
});

test('recordPath joins the data base with the record file', () => {
  assert.equal(recordPath('oracle-goldengate/23ai.json'), 'data/oracle-goldengate/23ai.json');
});
