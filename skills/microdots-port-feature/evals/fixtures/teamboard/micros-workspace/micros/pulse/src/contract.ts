import { Rpc, RpcGroup } from 'effect/unstable/rpc'
import { Schema as S } from 'effect'

export const Pulse = S.Struct({
  value: S.Number,
  at: S.Number,
})

export class PulseRpcs extends RpcGroup.make(
  Rpc.make('getPulse', { success: Pulse }),
) {}
