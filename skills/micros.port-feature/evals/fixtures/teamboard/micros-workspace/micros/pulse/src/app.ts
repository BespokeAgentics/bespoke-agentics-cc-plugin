// Foldkit program for the pulse ticker. The canonical minimal shape:
// AsyncData model with Refreshing so a poll never blanks a rendered value.
import { Match, Schema as S } from 'effect'

export const Model = S.Union(
  S.Struct({ _tag: S.Literal('Loading') }),
  S.Struct({ _tag: S.Literal('Loaded'), value: S.Number, refreshing: S.Boolean }),
  S.Struct({ _tag: S.Literal('Failed'), message: S.String }),
)

// Messages are facts, past tense.
// PulseArrived | PulseFailed | TickElapsed
// update: Match.tagsExhaustive over the union; a failed refresh keeps the
// last Loaded value (stale beats blank), only the initial load may Fail.
// subscriptions: Subscription.every(2000, TickElapsed)
// view: h.div([...]) hyperscript — omitted in this fixture excerpt.
export const note = Match
