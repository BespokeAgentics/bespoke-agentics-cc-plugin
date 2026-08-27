// RpcAppLayer = RpcServer.layerHttp + handlers + NDJSON serialization.
// No platform imports allowed in this file. Per-call gate wiring:
// handlers that touch gated data verify via SecretGate (fail-closed) first —
// see packages/kit-effect/src/secret.ts (SecretGate, makeSecretGateLive).
// Unauthorized is a tagged error on the contract, not an HTTP hack.
export const RpcAppLayer = 'fixture-stub'
