const COUPON_RATES = {
  SUMMER10: 0.1,
  FALL15: 0.15
};

export function applyDiscount(subtotal, couponCode) {
  const pct = COUPON_RATES[couponCode] ?? 0;
  return Math.round(subtotal - subtotal * pct);
}

export function applyLegacyDiscount(total, pct) {
  return Math.round(total - total * pct);
}
