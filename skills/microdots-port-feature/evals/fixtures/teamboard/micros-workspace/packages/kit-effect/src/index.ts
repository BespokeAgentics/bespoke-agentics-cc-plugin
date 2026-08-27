// Browser-only barrel. @kit/effect/service is Node-only; importing it from
// browser code drags node:http into the bundle.
export const makeRpcClientLive = (_baseUrl: string) => 'fixture-stub'
export const microAppCors = 'fixture-stub'
export const DEPLOYED_HOST_ORIGIN = 'https://example.workers.dev'
