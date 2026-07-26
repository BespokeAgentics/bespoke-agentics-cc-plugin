import { readFileSync } from 'node:fs';
import * as format from './format.js';

const config = JSON.parse(
  readFileSync(new URL('../receipt-config.json', import.meta.url), 'utf8')
);

export function printReceipt(lines) {
  return format[config.receipt.renderer](lines);
}
