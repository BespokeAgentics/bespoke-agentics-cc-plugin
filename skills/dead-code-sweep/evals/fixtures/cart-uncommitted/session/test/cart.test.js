import test from 'node:test';
import assert from 'node:assert/strict';
import { cartTotal } from '../src/cart.js';

test('cartTotal applies coupon rate', () => {
  const items = [{ name: 'mug', price: 1000, qty: 2 }];
  assert.equal(cartTotal(items, 'SUMMER10'), '$18.00');
});

test('cartTotal without coupon', () => {
  const items = [{ name: 'mug', price: 1000, qty: 2 }];
  assert.equal(cartTotal(items), '$20.00');
});
