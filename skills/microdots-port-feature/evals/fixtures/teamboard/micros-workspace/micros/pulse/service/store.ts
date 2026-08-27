// The store seam: one Context.Service interface, shared SQL strings, and one
// adapter per platform (storeD1.ts for Workers, storeSqlite.ts for Bun) so
// handlers.ts never names a platform package.
export const SQL_LATEST = 'SELECT value, at FROM pulses ORDER BY at DESC LIMIT 1'
export interface PulseStore {
  readonly latest: () => unknown
}
export const makeStoreSqlite = () => ({ latest: () => null })
export const changesOf = (r: unknown) => r
