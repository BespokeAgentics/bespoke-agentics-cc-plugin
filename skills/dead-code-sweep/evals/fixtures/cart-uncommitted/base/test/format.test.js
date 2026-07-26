import test from 'node:test';
import assert from 'node:assert/strict';
import { formatPrice } from '../src/format.js';

test('formatPrice renders dollars', () => {
  assert.equal(formatPrice(1850), '$18.50');
});
