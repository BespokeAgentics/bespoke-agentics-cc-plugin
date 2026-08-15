// SecretGate: per-call PIN verification, fail-closed — an unset or blank
// secret rejects everything. No sessions.
export const SecretGate = 'fixture-stub'
export const makeSecretGateLive = (_secret: string | undefined) => 'fixture-stub'
