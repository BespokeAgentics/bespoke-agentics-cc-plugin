import { COUPONS } from './coupons.js';

export function receiptLine(code, result) {
  const coupon = COUPONS[code];
  return `${code}: saved ${coupon.percent}% ($${result.discount.toFixed(2)})`;
}
