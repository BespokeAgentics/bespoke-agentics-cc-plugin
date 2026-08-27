---
name: microdots-design
description: Route visual and design work on a MicroDots workspace to the impeccable-microdots plugin, and state the boundary against the wireframe family. Use for "polish this dot", "the readout panel looks wrong", "audit this MicroDot's design", "critique the platform shell", "try some variants of this view", or any request to change how a MicroDot looks.
---

This skill is a router. It resolves the workspace, confirms the request belongs to `impeccable-microdots`, states the boundary against the neighbouring skills, and hands off. It deliberately does not restate design guidance: that lives in one place, and a second copy is what goes stale.

## 0. Resolve the workspace

Read these from the project. Never assume them.

| What | How |
|---|---|
| Dot directory | `microdots/` or `micros/`, whichever the root `package.json` `workspaces` declares |
| Is it a MicroDots workspace | a dot whose `src/element.ts` calls `defineMicroDot` (with type arguments, which every real dot passes) |
| Shells | workspace entries holding `index.html` AND `package.json`. `dist/` and `public/` have an `index.html` and are not shells |
| Shell ports | from `bun run dev` output, not from memory |
| Dot service port | each dot's own `package.json`, under `microdot.port`. Never inferred from a range |
| Theme package | `packages/microdots-theme` — the token vocabulary's source of truth |

If none of this resolves, this is not a MicroDots workspace. Say so and stop.

## 1. Route

**A MicroDots workspace, and the request is about how it looks:** use the `impeccable-microdots` plugin. Invoke `/impeccable-microdots:impeccable <command>`, or `/impeccable-microdots:impeccable live` for variants. It carries the framework reference, the vocabulary gate, the detector's token resolution, and the preview harness.

If the plugin is not installed, add its marketplace entry (it is already listed in this repo's `.claude-plugin/marketplace.json`) rather than doing the work here. Reproducing its guidance in this session is exactly the drift this skill exists to avoid.

**Not a MicroDots workspace:** use upstream Impeccable. The fork adds nothing for other stacks and its vocabulary rules are wrong there.

## 2. The three facts that change what a correct edit is

Enough to route well. The rest is in the plugin's own reference.

1. **The class vocabulary is a build gate, not a preference.** `packages/microdots-theme/src/palette-usage.test.ts` fails the build on `bg-white`, `text-slate-500`, and every palette literal. It compiles and renders; it just stops responding to `[data-theme]`. Nothing else can see that.
2. **Four Tailwind defaults are remapped and two invert.** `rounded-lg` is 14px. `tracking-tight` is *positive* button tracking. `text-xs` and `text-sm` do not exist and fail nothing while breaking the type scale.
3. **`Runtime.embed` swallows startup defects.** A broken dot renders blank with a clean console while typecheck, lint, tests and build all pass. `bun run check` green is necessary and not sufficient; the browser step is the proof.

## 3. Boundary against the neighbours

Four skills in this repo touch UI, and only one of them writes production code:

| Skill | What it does | Writes production code |
|---|---|---|
| `reimagine` | explores *which* design, as a variant gallery | no |
| `interactive-wireframe` | settles *the* design, as a spec | no |
| `wireframe-parity` | checks the build against the wireframe that specified it | no |
| `data-ui-craft` | fixes data-display craft in shipped UI | yes, without measuring |
| **`impeccable-microdots`** | **refines a MicroDot's actual views** | **yes, gated by `bun run check` and a render check** |

If the design is not settled yet, `interactive-wireframe` comes first. If the question is "what could this become", that is `reimagine`. `impeccable-microdots` refines something that exists.

## 4. What to expect from a live session

So the handoff sets accurate expectations rather than promising a loop this framework cannot give:

- Variants are **real view functions**, not spliced HTML, because Foldkit views are hyperscript.
- They render in a **generated harness**, not the composed shell: shells load built bundles and `defineMicroDot` refuses to redefine a registered tag, so a rebuilt bundle is silently discarded in a live page. A variant can look right in the harness and wrong in place.
- An edit **reloads the page** and restores the preserved Model. That is Foldkit's design, not a misconfiguration.
- The dot's service CORS names the shell origins, so until it allows the harness port the dot renders **only its error states** there.
- Accept writes source once, then runs format, `bun run check`, a dot build, and a render gate, restoring the file if any of them fails.

## 5. Finish

Report what was changed, which gates ran, and which states were actually reviewed. A state nobody reached is reported as **not reviewed**, never as passing. If the render gate reports `blank` or `startup-defect`, hand off to `microdots-debug-blank` rather than guessing: that is the framework's most expensive failure shape, and it has its own protocol.
