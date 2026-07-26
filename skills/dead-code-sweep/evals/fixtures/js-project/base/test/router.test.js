import test from 'node:test';
import assert from 'node:assert/strict';
import { dispatch } from '../src/router.js';

test('dispatches configured webhook route', async () => {
  const r = await dispatch('/hooks/github', { event: 'push' });
  assert.deepEqual(r, { status: 200, event: 'push' });
});

test('404s unknown routes', async () => {
  const r = await dispatch('/nope', {});
  assert.equal(r.status, 404);
});
