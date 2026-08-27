---
name: microdots-content
description: Research, write, and publish content mined from a MicroDots workspace's own git history and wiki — work-recap blog posts, changelogs/release notes, feature deep-dives, and social short-form — written in the brand voice with Mermaid diagrams where they earn their place, published as self-contained branded HTML. Use whenever the user asks to "write a blog post", "post about what we shipped", "recap this week's work", "write the changelog" or "release notes", "deep-dive on <MicroDot or feature>", "write a social post/thread about", or any request to turn repo history, a shipped plan, or a feature into publishable content — even when no format is named.
---

# MicroDots content generation

Turn what actually happened in this repo into publishable content. The whole
skill rests on one discipline: **every claim traces to a commit hash, a
`file:line`, or a wiki page.** The wiki holds itself to that standard
(`## Source References` on every page); content that leaves the repo is held to
it harder, because a reader cannot check the repo.

## Step 1 — Parse the ask

Extract three things from the request:

1. **Format** — recap post, changelog, deep-dive, or social. If unnamed, infer:
   time-scoped ask → recap post; "changelog"/"release notes" → changelog; a
   named feature or MicroDot → deep-dive. Templates for all four are in
   `references/formats.md` — **read it before writing.**
2. **Scope** — resolve relative dates ("yesterday", "this week") against today's
   date into a concrete `--since`/`--until` window, and **say the resolved
   window in the piece**. For a deep-dive, scope is the feature, not a window.
3. **Publish root** — resolve it, do not assume:

   ```bash
   ls -d apps/website site www public docs 2>/dev/null
   ```

   Use the invocation's override if given; else an existing site directory; else
   ask before creating one.

## Step 2 — Research

Run the research **before writing a single sentence of prose.** For a
time-scoped window:

```bash
git log --since=<start> --until=<end> --format='%h %ad %s%n%b' --date=short
git log --since=<start> --until=<end> --stat --format='%h'   # shape of each change
```

Then read, in order of authority — every wiki row below applies only where the
workspace has a `wiki/`:

| Source                              | Gives you                                          |
| ----------------------------------- | -------------------------------------------------- |
| `wiki/_log.md`                      | what was ingested/decided recently, in order       |
| `wiki/plans/shipped/` (recent)      | the why behind landed work, with its outcome       |
| `wiki/plans/active/`                | context for in-flight work — label it as in-flight |
| `wiki/marketing/_index.md`          | the positioning language — what the product _is_   |
| `wiki/patterns-and-traps/` (if hit) | the story of a trap is often the best material     |
| `AGENTS.md` / `CLAUDE.md`           | the one-line identity of every MicroDot and its port |

No wiki: the commits and the code are all you have — say so in the report, and
keep the piece proportionally shorter rather than padding it with inference.

For a deep-dive: the MicroDot's own directory (**`contract.ts` first — it is the
public surface**), its `wiki/examples/<name>.md` page, and the plan that
produced it.

Commits are the skeleton; the wiki is the muscle. A commit says _what_; the plan
page says _why_ and _what it cost_ — that second layer is what makes the writing
worth reading. If the window has no commits, widen it once, say so, and **ask
before inventing a story.**

## Step 3 — Write

Voice is **hybrid narrative**: story-first for a developer who has never seen
this repo, grounded by real specifics.

- Open with what changed and why a reader should care. One paragraph, no
  throat-clearing.
- Specifics persuade; adjectives do not. "Fifteen services on ports 3101–3116"
  beats "a large fleet of services". Prefer the number, the port, the filename —
  **taken from the repo, never remembered.**
- Expand the first use of every internal term (MicroDot, Foldkit, the host, the
  broker). After that, use the term plainly.
- Machine-produced strings — hashes, ports, paths, tags, versions — render in
  mono on the page. **Never paraphrase a hash.**
- Cut any sentence you cannot trace to a source. No hype, no emoji, no
  exclamation marks.

## Step 4 — Diagrams

Include a diagram only when it shows a mechanism prose handles poorly — service
topology, a sequence across the broker, a before/after structure. Never
decorative. Use Mermaid inside the brand shell (`<pre class="mermaid">`) — the
shell's module already re-themes it on theme toggle, so **write Mermaid without
hardcoded colors.**

## Step 5 — Build the page

The design is already decided — do not restyle it. Build from the
`microdots-brand-recap` skill's assets by path:

1. Copy `${CLAUDE_PLUGIN_ROOT}/skills/microdots-brand-recap/assets/shell.html`
   verbatim as the starting file.
2. Paste `assets/tokens.css` into the `<style>` block first, then
   `assets/components.css` after it — **source order is the theme switch.**
3. Read
   `${CLAUDE_PLUGIN_ROOT}/skills/microdots-brand-recap/references/design-rules.md`
   before writing markup. Its six rules (one accent, hairlines, mono for data,
   no resting shadows, motion budget, no emoji) all bind here.

Each page is **fully self-contained** — inline CSS, no shared stylesheet. That
mirrors the framework's own bundle invariant and means a post never breaks when
the site around it changes.

## Step 6 — Publish

```
<publish-root>/
├── index.html                        listing page — newest first
└── posts/
    ├── <yyyy-mm-dd>-<slug>.html      the piece, self-contained
    └── <yyyy-mm-dd>-<slug>.social.md short-form copy, only when asked
```

- **First run:** the publish root is empty — scaffold `index.html` from the same
  shell, with a card per post (title, date, one-line summary, format tag).
- **Every run:** write the post, then add or refresh its card in `index.html`.
- Social copy is plain markdown next to the post: up to 3 variants, each
  standalone, derived from the researched facts — **never claims that exist only
  in the social copy.**

## Verify before reporting done

Open the published file in a browser and check: both themes render (toggle
works), every Mermaid diagram draws **and its labels are not truncated**, no
horizontal scroll at 320px, the index card links resolve. Then re-read the piece
once as a stranger — every claim should either carry its source or be obviously
derived from one.
