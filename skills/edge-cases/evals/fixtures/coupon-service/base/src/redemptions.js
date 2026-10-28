import { COUPONS } from './coupons.js';

const uses = new Map();

export async function redeem(code, userId, store) {
  const coupon = COUPONS[code];
  const count = uses.get(code) ?? 0;
  if (count >= coupon.maxUses) throw new Error('Coupon fully redeemed');
  await store.recordRedemption(code, userId);
  uses.set(code, count + 1);
}
