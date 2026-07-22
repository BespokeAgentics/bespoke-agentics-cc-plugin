# Grounding playbook

Read before Phase 1. The job: extract the real values this surface is made of,
from real source, with paths. Never invent one.

## Why this is the whole game

A wireframe built on invented values is decoration — it can only illustrate an
idea you already had. A wireframe built on real values is **predictive**: it
tells you things you did not know.

Only real values expose:

- **Collisions** — the project name and the nav tabs turn out to be the same
  size and weight, so they read as peers. Invisible in prose, obvious on screen.
- **Real widths** — the longest status label is 40% wider than the shortest, so
  everything after it shifts between records. You cannot see that with `Lorem`.
- **Real contrast** — a tint that looks fine is 3.9:1 and fails AA at that size.
- **Real cardinality** — "a few tabs" is nine tabs, and they wrap.

The cost of getting this wrong is worse than a bad mockup: the user makes a
decision against a picture that does not match their product, and the spec
inherits it.

## What to extract

**Cache first.** If `<out>/_index.md` exists, a previous run already grounded
the run-independent slice — tokens, typography, roles, anchors. Start from
`_library/grounding-cache.md` per the TTL rules in `references/reuse-library.md`
and extract fresh only what is surface-specific (its enums, extremes,
behavioural constants). `--fresh` skips the cache.

| # | Category | Why the wireframe needs it |
|---|----------|---------------------------|
| 1 | **Design tokens** — colour, spacing, radius, elevation, borders | The surface must sit in the product's palette, and contrast must be measurable |
| 2 | **Typography** — families, sizes, weights, tracking | Type metrics decide whether two labels collide or read as a hierarchy |
| 3 | **Enums, labels, statuses** — the literal strings displayed | Real longest-case strings drive layout; invented ones lie about width |
| 4 | **Roles / personas / permission flags** | Becomes the role axis: "what does an engineer see here" is a dropdown, not a paragraph |
| 5 | **Existing layout components** the change touches | Reveals what already owns the space, what is sticky, what z-index is in play |
| 6 | **Behavioural constants** — breakpoints, scroll thresholds, durations, z-index scale | Becomes the threshold axes; also stops the wireframe inventing a 3rd source of truth |
| 7 | **Data shape** — cardinality, nullability, extremes | Drives the empty / one / many / overflow states worth showing |

Categories 3 and 4 are the ones most often skipped and most often decisive.

## Where to look, by ecosystem

Detect the stack first (`package.json`, `Gemfile`, `*.csproj`, `go.mod`,
`pyproject.toml`, config files at root), then read the matching row. Most repos
match more than one — read them all and note which wins at runtime.

| Signal | Tokens live in |
|---|---|
| `tailwind.config.{js,ts,cjs}` | `theme.extend.colors / fontFamily / spacing / screens`. Tailwind v4: `@theme` in the main CSS file |
| `*.css` / `*.scss` with `:root` | CSS custom properties — usually the truest source |
| `styled-components`, `emotion`, `stitches` | `ThemeProvider` value / `createStitches` config |
| `@mui/material`, `chakra`, `mantine` | `createTheme(...)` / `extendTheme(...)` overrides — the diff from the default is what matters |
| shadcn/ui | `globals.css` `:root` + `.dark`, and `components.json` |
| `*.scss` / `*.less` | `$vars` / `@vars`, usually `_variables` or `_tokens` |
| Style Dictionary / `tokens.json` / `*.tokens` | Design-token JSON; find the build output that actually ships |
| Design-system package (`packages/ui`, `@org/design-system`) | Its own tokens file — prefer this over app-level overrides |
| Rails / ERB / ViewComponent | `app/assets/stylesheets`, `tailwind.config.js`, or a component library gem |
| Svelte / SvelteKit | `app.css`, `:root` in `+layout.svelte`, `app.html` |
| Vue / Nuxt | `assets/css`, `nuxt.config` theme, or a UI-kit config |
| Static site / no framework | The one stylesheet. Read it end to end |

Useful sweeps (adapt the paths, exclude vendor dirs):

```sh
rg -n --glob '!node_modules' -e '^\s*--[a-z0-9-]+\s*:' -g '*.css' -g '*.scss' | head -60
rg -n --glob '!node_modules' -e 'colors\s*:|fontFamily\s*:|screens\s*:' -g 'tailwind.config.*'
rg -n --glob '!node_modules' -e 'as const|^\s*export (const|enum) [A-Z_]+' -g '*.ts' | head -40
rg -n --glob '!node_modules' -e 'STATUS|_LABEL|_ORDER|Role|Persona|permission|can[A-Z]' -g '*.{ts,tsx,js,rb,py,go}' | head -60
```

For enums prefer the **label map** the UI actually renders (`STATUS_LABEL`,
`humanize`, an i18n bundle) over the raw DB enum — `in_review` is not what the
user sees, `Internal Review` is, and only one of them has the right width.

## When there is no design system

Say so explicitly — do not fill the gap with plausible-looking hexes. Two honest
options, in order of preference:

**1. Derive from the running app.** If the app runs, open the real surface and
read computed styles. This is ground truth even when nothing is written down:

```js
// paste into the browser console on the real page
const el = document.querySelector('<the surface>');
const cs = getComputedStyle(el);
({ color: cs.color, background: cs.backgroundColor, font: cs.font,
   border: cs.borderColor, radius: cs.borderRadius });

// or harvest the palette actually in use, ranked by frequency
const tally = {};
document.querySelectorAll('*').forEach(n => {
  const s = getComputedStyle(n);
  [s.color, s.backgroundColor, s.borderTopColor].forEach(v => {
    if (v && v !== 'rgba(0, 0, 0, 0)') tally[v] = (tally[v] || 0) + 1; });
});
Object.entries(tally).sort((a,b) => b[1]-a[1]).slice(0, 20);
```

**2. Derive from a screenshot** if the app cannot be run — sample the dominant
colours and state that they are sampled, not sourced.

Either way, label the token block `/* derived from computed styles — no design
system found */` so nobody later mistakes it for a contract.

## Honesty rules

- **Cite the path** next to every value. It goes into the wireframe as a
  comment, into the control overlay as the `from:` hint, and into the spec.
- **A missing token beats an invented one.** Omitted, someone asks. Invented, it
  looks authoritative and gets copied into production.
- **Mark derived values as derived.** Sampled ≠ sourced.
- **Prefer the value that ships.** An app-level override beats the design-system
  default; the built output beats the source when they disagree.
- **Note contradictions instead of picking a winner.** Two token files that
  disagree is itself a finding worth reporting.

## Output: `grounding.md`

Write this next to the wireframe before building anything. It is the audit trail
for every value in the file, and the spec cites it.

```markdown
# Grounding — <surface name>

**Stack:** <framework> · <styling> · <component library or "none">
**Surface:** <route / component / page>, rendered by `<path>`
**Confidence:** sourced | partly derived | derived (no design system)

## Tokens (cached — verified <date> · `_library/grounding-cache.md`)   <!-- heading form when reused from the cache; plain "## Tokens" when grounded fresh -->
| Token | Value | Source |
|---|---|---|
| `--surface` | `#fcfcfc` | `packages/ui/styles/tokens.css:12` |

## Typography
| Role | Family / size / weight | Source |

## Enums and labels
| Set | Values (verbatim) | Source |
| Order status | Draft · Submitted · In Review · Fulfilled | `src/lib/orders.ts:31` |

## Roles / permissions
| Role | Source | What it changes on this surface |

## Existing layout this touches
| Component | Path | Current behaviour (sticky? width? z-index?) |

## Gaps
- <what could not be found, and what the wireframe does instead>
```

The **Gaps** section is not optional. It is where "we could not find a token for
X, so the wireframe uses a neutral grey" gets said out loud, and it usually turns
into an interview question.
