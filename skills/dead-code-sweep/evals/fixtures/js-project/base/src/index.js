import './polyfill.js';
import { sendAlert } from './alerts.js';
import { mean } from './stats.js';

export function alertIfSlow(samplesMs, thresholdMs) {
  const avg = mean(samplesMs);
  if (avg > thresholdMs) {
    return sendAlert(`p50 latency ${avg}ms exceeds ${thresholdMs}ms`);
  }
  return null;
}
