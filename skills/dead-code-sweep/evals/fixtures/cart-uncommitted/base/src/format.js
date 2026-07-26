export function formatPrice(totalCents) {
  return `$${(totalCents / 100).toFixed(2)}`;
}

export function renderReceipt(lines) {
  return lines.join('\n');
}
