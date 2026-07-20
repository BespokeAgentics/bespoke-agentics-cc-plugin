# Hard-gate proofs — declaring and proving server-authoritative invariants

A **hard gate** is the strongest kind of guardrail: an invariant that must hold at the
**authoritative layer** of the system, provable by adversarial input, not merely observed in the UI.
It generalizes the archetype *"a crafted per-feature override must not be able to force a
`Not-available` tab on, enforced in the server-side resolution function — not client CSS."*

Most guardrails are checked by a human reading a diff. A hard gate is different: the validator must
**actively try to break it** and produce evidence that it held. This is the skill's signature rigor
and the concrete form of "attack your own conclusion before handing it over".

## Declaring a hard gate (in the contract)

```
{ id, statement, enforced_at, proof_method }
```

- **id** — `HG-1`, `HG-2`, …
- **statement** — the invariant, in the **negative form that names the attack**: "a crafted X cannot
  force Y", "no input to fn Z yields state W". Negative framing makes the proof falsifiable.
- **enforced_at** — the **authoritative function/file** where the invariant must live: the
  server-side resolver, the persistence boundary, the policy function. If the only enforcement is
  client-side, that itself is the finding — the hard gate is not yet real.
- **proof_method** — the concrete adversarial test: the crafted input, the call, and the assertion on
  the output at `enforced_at`.

## Proving or refuting it (the validate phase)

The validator must return, for each hard gate, a **proof artifact** — never a verdict alone:

```
## Hard-gate proofs
| id   | verdict          | authoritative layer confirmed        | proof artifact |
|------|------------------|--------------------------------------|----------------|
| HG-1 | proved           | src/lib/.../resolve.ts::resolveTabs   | crafted override {tab:"x",state:"show"} where x is N/A; resolveTabs() returned [...] omitting x — see reports/ws-2-validate-a1.md |
```

- **proved** — the validator crafted the adversarial input, exercised `enforced_at` **directly** (a
  unit call / focused test, not a UI click), and observed the invariant hold. The artifact records
  the input, the call, and the observed output.
- **refuted** — the validator found an input that breaks the invariant, OR found the invariant is
  enforced only downstream of the authoritative layer (e.g. hidden in the client while the server
  still emits it). Either way ⇒ `pass: false` for the workstream.

## Why "hidden in the UI" is never a proof

If the invariant is enforced only by client markup/CSS, any consumer that bypasses the client — a
direct API call, a second UI, a future refactor — re-opens the hole. A hard gate exists precisely to
survive that. So the proof must exercise the **authoritative layer in isolation** and show the bad
input is neutralized there. A workstream whose hard gate is only client-enforced fails validation
even when every visible gate is green.

## Writing the proof as a durable test

Prefer a proof that leaves a **regression test** behind: a focused unit test against `enforced_at`
that feeds the adversarial input and asserts the safe output. That way the hard gate is re-proved on
every future run of the gates, not just once. When a durable test isn't feasible, the validator's
recorded call + output in `reports/` is the artifact — but note in the finding that the proof is
one-shot, not regression-guarded.

## When a plan has no hard gates

Not every plan needs one. If the plan declares none and you infer none (no server-authoritative
invariant is at stake), record "Hard gates: none" in the contract and skip the proof column — do not
manufacture ceremony. But look first: any "must never be possible" statement about a
security / permission / visibility boundary is usually a hard gate in disguise.
