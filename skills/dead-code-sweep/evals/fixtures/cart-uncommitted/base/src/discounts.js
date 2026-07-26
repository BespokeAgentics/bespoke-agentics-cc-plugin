export function applyLegacyDiscount(total, pct) {
  return Math.round(total - total * pct);
}
