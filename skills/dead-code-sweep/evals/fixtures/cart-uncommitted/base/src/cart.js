import { applyLegacyDiscount } from './discounts.js';
import { formatPrice } from './format.js';
import { formatCents } from './money.js';
import { SEASONAL_CODES } from './coupon-codes.js';

export function cartTotal(items, couponCode) {
  let total = items.reduce((sum, it) => sum + it.price * it.qty, 0);
  if (couponCode && SEASONAL_CODES[couponCode]) {
    total = applyLegacyDiscount(total, SEASONAL_CODES[couponCode]);
  }
  return formatPrice(total);
}

export function lineItem(item) {
  return `${item.name}: ${formatCents(item.price * item.qty)}`;
}
