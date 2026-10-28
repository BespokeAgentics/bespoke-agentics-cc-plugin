// Coupon rules, from the promo brief:
//   "Orders of $50 or more qualify for SAVE10."
//   "Codes are case-insensitive."
//   "A coupon is valid through the end of its expiry date."
export const COUPONS = {
  SAVE10: { percent: 10, minSubtotal: 50, expires: '2026-12-31', maxUses: 1000 },
  WELCOME5: { percent: 5, minSubtotal: 0, expires: '2027-06-30', maxUses: 1 },
};

export function subtotalOf(cart) {
  return cart.items.reduce((sum, item) => sum + item.price * item.qty, 0);
}

export function applyCoupon(cart, code, now = new Date()) {
  const coupon = COUPONS[code];
  if (!coupon) throw new Error('Invalid coupon code');
  if (now > new Date(coupon.expires)) {
    throw new Error('Coupon expired');
  }
  const subtotal = subtotalOf(cart);
  if (subtotal > coupon.minSubtotal) {
    const discount = (subtotal * coupon.percent) / 100;
    return { subtotal, discount, total: subtotal - discount };
  }
  return { subtotal, discount: 0, total: subtotal };
}
