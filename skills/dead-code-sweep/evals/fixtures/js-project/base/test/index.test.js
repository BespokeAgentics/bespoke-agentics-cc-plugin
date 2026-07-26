import test from 'node:test';
import assert from 'node:assert/strict';
import { alertIfSlow } from '../src/index.js';

test('alerts when mean exceeds threshold', () => {
  const r = alertIfSlow([300, 400], 250);
  assert.match(r.message, /exceeds 250ms/);
});

test('quiet when under threshold', () => {
  assert.equal(alertIfSlow([100, 120], 250), null);
});
