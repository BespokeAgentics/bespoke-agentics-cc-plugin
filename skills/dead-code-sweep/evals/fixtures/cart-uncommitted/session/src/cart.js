import { applyDiscount } from './discounts.js';
import { formatPrice } from './format.js';
import { formatCents } from './money.js';

export function cartTotal(items, couponCode) {
  const subtotal = items.reduce((sum, it) => sum + it.price * it.qty, 0);
  return formatPrice(applyDiscount(subtotal, couponCode));
}

// Old implementation kept for reference during the migration:
// export function cartTotalLegacy(items, couponCode) {
//   let total = items.reduce((sum, it) => sum + it.price * it.qty, 0);
//   if (couponCode && SEASONAL_CODES[couponCode]) {
//     total = applyLegacyDiscount(total, SEASONAL_CODES[couponCode]);
//   }
//   return formatPrice(total);
// }
