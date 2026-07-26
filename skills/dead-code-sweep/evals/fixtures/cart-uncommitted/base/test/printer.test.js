import test from 'node:test';
import assert from 'node:assert/strict';
import { printReceipt } from '../src/printer.js';

test('printReceipt joins lines via configured renderer', () => {
  assert.equal(printReceipt(['a', 'b']), 'a\nb');
});
