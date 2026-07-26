export function toCsv(rows) {
  return rows.map((r) => r.join(',')).join('\n');
}
