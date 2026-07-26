#!/usr/bin/env node
import { alertIfSlow } from './index.js';

const samples = process.argv.slice(2).map(Number);
const result = alertIfSlow(samples, 250);
console.log(result ? result.message : 'ok');
