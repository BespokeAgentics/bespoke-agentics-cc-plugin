# The Current baseline — recreation as a grounding product

Read before Phase 1. The Current pane is what every variant is judged against;
if it is wrong, every comparison in the gallery is wrong. Recreating it is a
**grounding act, not a design act** — nothing in it is chosen, everything in it
is transcribed.

## Extraction recipe

1. **Structure from source.** Read the real component (JSX / template / Astro /
   HTML), transcribe its element tree, landmark order, and band structure into
   the `rv-current` pane. Every structural claim gets a `path:line` row in
   `grounding.md` under a **"Baseline fidelity"** section. Where the component
   composes children, follow the imports far enough to get the rendered
   structure right — a baseline that flattens a real sub-component into a div
   misstates what Restructure variants are departing from.
2. **Values from grounding.** Tokens and typography come from the shared
   REPLACE 1 block (cache-first per the parent's `references/reuse-library.md`
   TTL rules). Labels, enums, and empty-state copy are transcribed **verbatim**
   from source — not paraphrased.
3. **Data from extremes.** Rows/records use the grounded longest-case strings,
   so Current exhibits the same stress the variants must survive.
4. **Approximations are listed, not hidden.** Icon fonts, third-party widget
   internals, canvas/map content, and anything else transcription cannot reach
   are recorded in grounding.md as `approximated: <what> — <why>` and repeated
   in the spec's Baseline fidelity statement.

If a prior run left a `grounding.md` in the slug directory, treat it as a warm
cache (TTL rules apply) and extend it in place with a dated reimagine section
rather than starting a parallel file.

## The optional cross-check (`--baseline-url`)

If the user has the app running, ask once for the URL — **never boot the app**.
Inject wireframe-parity's probe (reused in place:
`skills/wireframe-parity/assets/wf-probe.js`) into the live page and diff a
small fixed set against the Current pane:

- band order and heights (`bands` on the same regions)
- 2–3 key contrast pairings
- rendered label texts (`texts`)

Record deltas in grounding.md. A delta means the *source read* was wrong or the
app renders something source doesn't show (feature flag, runtime theming) —
either way it is information, not embarrassment. Declined or unavailable is
fine; the fidelity chip just says so.

## The fidelity chip — labels never lie

The manifest's `fidelity` field renders on the Current pane head in grid/split
view. Exactly two honest values:

- `Recreation — cross-checked <YYYY-MM-DD>` — the wf-probe diff ran against the
  live app and deltas (if any) are in grounding.md
- `Recreation — code-grounded, not pixel-checked` — structure/tokens/labels from
  source only

The baseline claims **structural + token + label fidelity, never pixel
fidelity** — the chip says which was verified. The same statement, plus the
approximations list, appears in the spec so a reader six weeks later knows how
much to trust the Δ inventory's "Current" column.
