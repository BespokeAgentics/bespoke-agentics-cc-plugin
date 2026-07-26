import test from 'node:test';
import assert from 'node:assert/strict';
import { applyLegacyDiscount } from '../src/discounts.js';

test('applyLegacyDiscount takes a percentage off', () => {
  assert.equal(applyLegacyDiscount(2000, 0.1), 1800);
});
