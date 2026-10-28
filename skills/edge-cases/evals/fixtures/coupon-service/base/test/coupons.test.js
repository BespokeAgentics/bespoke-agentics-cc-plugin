import { test } from 'node:test';
import assert from 'node:assert/strict';
import { applyCoupon } from '../src/coupons.js';

test('SAVE10 takes 10% off an $80 order', () => {
  const cart = { items: [{ price: 40, qty: 2 }] };
  const result = applyCoupon(cart, 'SAVE10', new Date('2026-06-01T12:00:00Z'));
  assert.equal(result.discount, 8);
  assert.equal(result.total, 72);
});
