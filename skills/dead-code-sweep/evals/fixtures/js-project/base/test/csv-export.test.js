import test from 'node:test';
import assert from 'node:assert/strict';
import { toCsv } from '../src/csv-export.js';

test('joins rows with commas and newlines', () => {
  assert.equal(toCsv([['a', 'b'], ['c', 'd']]), 'a,b\nc,d');
});
