import test from 'node:test';
import assert from 'node:assert/strict';
import { cartTotal, lineItem } from '../src/cart.js';

test('cartTotal applies seasonal coupon', () => {
  const items = [{ name: 'mug', price: 1000, qty: 2 }];
  assert.equal(cartTotal(items, 'SUMMER10'), '$18.00');
});

test('lineItem renders name and cents', () => {
  assert.equal(lineItem({ name: 'mug', price: 1000, qty: 1 }), 'mug: 1000¢');
});
