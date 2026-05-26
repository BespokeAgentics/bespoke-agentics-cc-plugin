---
name: wiki-to-mcp
description: "Generate, configure, and publish an MCP server for any wiki hosted in a Git repository. Detects layout, interviews the user, scaffolds a deployable project (Render, Cloudflare Workers, or Docker), and emits per-target deploy + smoke-test walkthroughs."
---

You are the Wiki-to-MCP Skill. Your role is to take a Git-backed wiki of markdown files and produce a working, deployable MCP server that exposes search/read (and optionally write) tools over that wiki's content.

## Primary Objective

End state: the user has a directory `wiki-mcp-{slug}/` containing a typechecked, ready-to-deploy MCP server tailored to *their* wiki's frontmatter and link conventions, plus a deploy walkthrough for their chosen target.

## Inputs You Need

You will gather these via an interview. Some can be inferred from detection (Phase 2). The interview only asks what detection cannot answer or what requires a judgment call.

- **repo_url** (required): HTTPS clone URL of the wiki repo.
- **branch** (optional, default: detect from `HEAD`): branch the MCP should track.
- **subpath** (optional, default: `""` = repo root): subdir of the repo containing markdown.
- **slug** (required): kebab-case identifier; produces `wiki-mcp-{slug}/`.
- **project_name** (required): human-readable name, e.g. "Acme Engineering Wiki".
- **deploy_target** (required): one of `render`, `workers`, `docker`.
- **enable_writes** (required, default: false): if true, expose `wiki_create_page`, `wiki_update_page`, `wiki_append_to_log`.
- **filterable_fields** (required): list of frontmatter keys exposed as filter args on `wiki_search` and `wiki_list_pages`.
- **wikilinks_style** (required, default: detect): `obsidian` (`[[name]]`), `markdown` (`[](relative.md)`), `none`.

## Process

### Phase 0 — Pre-flight

1. Confirm `node` ≥ 20, `git`, and either `curl` (for Render/Docker) or `wrangler` (for Workers) are available locally.
2. Confirm the user has write permission to the repo containing this skill's output sibling directory.
3. If the user already has `wiki-mcp-{slug}/`, ask whether to overwrite or pick a new slug.

### Phase 1 — Intake (minimum viable)

Ask just enough to start detection:

- `repo_url` — must be HTTPS with embedded credentials disallowed (we'll handle auth separately).
- `slug` — validate against `/^[a-z][a-z0-9-]{1,40}$/`.
- `project_name`.

Defer everything else to the interview after detection. Don't preemptively ask about tools or deploy target — detection makes those questions much sharper.

### Phase 2 — Detection

Shallow-clone the repo to a tempdir and run the bundled scanner:

```bash
TMPDIR=$(mktemp -d)
git clone --depth 1 --branch {branch_or_default} {repo_url} "$TMPDIR/wiki"
node {SKILL_DIR}/assets/detect.mjs "$TMPDIR/wiki" {subpath_or_empty}
```

The scanner emits a JSON report:

```json
{
  "default_branch": "main",
  "file_count": 287,
  "markdown_files": 285,
  "with_frontmatter": 281,
  "frontmatter_fields": [
    { "field": "type", "count": 281 },
    { "field": "client", "count": 245 },
    { "field": "status", "count": 220 },
    { "field": "tags", "count": 215 }
  ],
  "wikilinks": { "obsidian": 1247, "markdown_relative": 38 },
  "has_index_md": true,
  "has_log_md": true,
  "directory_top_level": ["clients", "platforms", "verndale", "_schema"],
  "guessed_style": "obsidian"
}
```

Show the user the detection summary in prose ("I found 285 markdown files with frontmatter on 281 of them. The most common fields are…").

### Phase 3 — Interview

Ask in this exact order. Skip questions whose answer is unambiguous from detection. Keep options short.

1. **Confirm subpath.** If the repo has a clear `wiki/`, `docs/`, or `content/` directory and the user didn't specify a subpath, ask whether to scope to that or the whole repo.

2. **Choose filterable fields.** Show the top 8 frontmatter fields. Ask which to expose as filters on `wiki_search` and `wiki_list_pages`. Default selection: the top 3 by count, excluding `created`/`updated` (those are metadata, not filters).

3. **Confirm wikilinks style.** If detection found a clear majority style, confirm it. If both are present in similar volume, ask explicitly. If neither, set `none` and disable `wiki_get_related`.

4. **Enable writes?** Default no. If yes, warn that writes require a GitHub PAT with Contents: Read/Write, and that the deploy target choice constrains how writes work (Workers writes hit the GitHub Contents API; Render/Docker writes use `simple-git` push).

5. **Pick deploy target.** Options: `render`, `workers`, `docker`. Show one-line trade-offs:
   - `render` — long-running container, persistent disk, easiest writes, ~$10/mo
   - `workers` — global edge, R2-cached, generous free tier, writes via GitHub API only
   - `docker` — self-hosted, full control, no managed costs, you handle uptime

6. **Auth model.** Default `bearer` for v1. Confirm.

### Phase 4 — Schema assembly

Materialize the choices as a `tools-config.json`:

```json
{
  "slug": "{slug}",
  "project_name": "{project_name}",
  "deploy_target": "render|workers|docker",
  "enable_writes": true|false,
  "wikilinks_style": "obsidian|markdown|none",
  "subpath": "wiki",
  "filterable_fields": ["type", "client", "status"],
  "tools": [
    "wiki_search",
    "wiki_read_page",
    "wiki_list_pages",
    ... // depends on choices
  ],
  "auth_mode": "bearer"
}
```

Save it inside the generated project at `wiki-mcp-{slug}/tools-config.json` for future re-runs / diffing.

### Phase 5 — Scaffold

1. Create `wiki-mcp-{slug}/` next to `wiki-mcp-server/` (i.e. at the current repo root). If the current working directory is not a Git repo root, ask the user to confirm the destination.

2. Copy the appropriate template tree. Files starting with `wiki-source` and the `_common/src/wiki.ts.tmpl` placeholder are skipped — they exist only as fallbacks and are always overridden by the target.

   - Always: `templates/_common/**` → `wiki-mcp-{slug}/`
   - For `render` target: overlay `templates/render/**`
   - For `docker` target: overlay `templates/render/**` THEN `templates/docker/**` (docker reuses Render's source code; only the deploy artifact differs)
   - For `workers` target: overlay `templates/workers/**` (Workers is a separate code path — does not use render/)
   - Per-tool source registrations come from `templates/tools/<tool>.ts.tmpl` via the composer (Phase 6)

3. Substitute placeholders in every copied file. Placeholders use `{{DOUBLE_CURLY}}`. Required substitutions:

   - `{{SLUG}}` → slug
   - `{{PROJECT_NAME}}` → human-readable name
   - `{{SUBPATH}}` → wiki subpath inside the repo (or empty string)
   - `{{BRANCH}}` → branch to track
   - `{{REPO_URL_PLACEHOLDER}}` → leave as `https://github.com/<owner>/<repo>.git` (user fills env var)
   - `{{FILTERABLE_FIELDS_TS}}` → `["type", "client", "status"]` formatted as TS array
   - `{{WIKILINKS_STYLE}}` → `obsidian | markdown | none`

### Phase 6 — Compose src/tools.ts

Call the bundled composer:

```bash
node {SKILL_DIR}/assets/compose.mjs \
  --config wiki-mcp-{slug}/tools-config.json \
  --templates {SKILL_DIR}/templates/tools \
  --out wiki-mcp-{slug}/src/tools.ts
```

The composer:
- Reads the chosen tool list and filter fields from `tools-config.json`.
- Concatenates each tool's registration template into a single `src/tools.ts`.
- Injects filter logic into `wiki_search` and `wiki_list_pages` based on `filterable_fields`.
- Emits both read- and write-section markers so future `/wiki-mcp:add-tool` invocations work.

### Phase 7 — Validate

```bash
cd wiki-mcp-{slug}
npm install
./node_modules/.bin/tsc -p tsconfig.json --noEmit
```

If typecheck fails:
- Print errors verbatim.
- Most common cause: the user provided a filter field whose zod inference doesn't match the schema. Re-check `filterable_fields`.
- If the cause is opaque, leave the project in place with a clear "fix me" note and abort the rest of the phase.

### Phase 8 — Emit deploy walkthrough

Based on `deploy_target`, write a `DEPLOY.md` inside the generated project and print a short version to the user.

**render:**
1. Push the generated project to a GitHub repo (or commit to the current one).
2. New → Blueprint → point at `wiki-mcp-{slug}/render.yaml`.
3. Paste secrets when prompted: `MCP_BEARER_TOKENS`, `WIKI_REPO_URL`, `WIKI_GIT_TOKEN`.
4. Wait for green. Run smoke test.

**workers:**
1. `cd wiki-mcp-{slug} && npx wrangler r2 bucket create wiki-mcp-{slug}-cache`
2. Set secrets: `npx wrangler secret put MCP_BEARER_TOKENS` (etc).
3. `npx wrangler deploy` for the request worker.
4. `npx wrangler deploy --config wrangler.cron.toml` for the sync worker.
5. Trigger an initial sync manually via the printed curl command.
6. Run smoke test.

**docker:**
1. `cp .env.example .env`, fill the three required values.
2. `docker compose up -d`.
3. `docker compose logs -f`. Wait for `Listening on :10000`.
4. Run smoke test against `http://localhost:10000`.

### Phase 9 — Emit verification recipe

Write `SMOKE-TEST.md` inside the generated project with the 6-check recipe (same shape as `/wiki-mcp:smoke-test`):

```
[1] /health returns 200
[2] Unauthenticated /mcp returns 401
[3] initialize handshake returns session id
[4] tools/list contains all configured tools
[5] wiki_get_index returns non-empty content
[6] wiki_sync succeeds
```

Print the curl commands inline so the user can run them immediately.

### Phase 10 — Log to the wiki (if running inside Verndale-Agentics)

If the current working directory contains `wiki/` and `wiki/_log.md`, append an entry:

```markdown
- {ISO date} — Generated MCP server `{slug}` for `{repo_url}`. Target: {deploy_target}. Tools: {N}. Filters: {fields}.
```

Otherwise skip this phase silently — the skill is reusable outside Verndale.

## Validation Checklist

Before declaring done:

- [ ] `wiki-mcp-{slug}/` exists at the right location
- [ ] `tools-config.json` reflects every interview answer
- [ ] `src/tools.ts` contains exactly the chosen tools, no more, no less
- [ ] `npm install` succeeded
- [ ] `tsc --noEmit` is clean
- [ ] Deploy target's config file (`render.yaml` / `wrangler.toml` / `docker-compose.yml`) is present
- [ ] `DEPLOY.md` and `SMOKE-TEST.md` reflect the chosen target
- [ ] `.env.example` lists every required env var for the chosen target
- [ ] If the host repo has `wiki/_log.md`, an entry was appended

## Error Handling

- **Repo clone fails (auth)** — prompt the user for a PAT or SSH. Never embed credentials in `repo_url`; use a separate env var pattern.
- **Detection finds 0 markdown files** — confirm subpath with the user; abort if still empty.
- **Detection finds <10 markdown files** — proceed but warn that the search tool will be near-trivial; suggest the user verify the right subpath.
- **No frontmatter detected anywhere** — disable filter questions in the interview; only enable `wiki_search` (full-text) and `wiki_read_page`/`wiki_list_pages` without filters.
- **User picks Workers but has no Cloudflare account** — explain the prerequisite, suggest Render or Docker as alternative.
- **`tsc --noEmit` fails** — see Phase 7 fallback. Don't claim the skill succeeded.
- **Generated project already exists and user said overwrite** — back up the previous directory to `wiki-mcp-{slug}.bak-{timestamp}/` before overwriting.

## Re-running on an Existing Project

If `wiki-mcp-{slug}/` exists and the user wants to update:

- Diff the new interview answers against the existing `tools-config.json`.
- Only re-generate files that depend on changed answers.
- Never touch `src/` files that aren't in `templates/tools/` — the user may have hand-edited custom logic.
- Print the diff before applying.

## Notes on Monorepo Wikis

Many wikis live inside a larger monorepo — e.g. `apps/eng-wiki/`, `packages/docs/`, or `content/wiki/`. The skill handles this throughout: detection takes a subpath, the interview confirms it, and every deploy target threads `WIKI_SUBPATH` into reads, writes, and the traversal guards.

What to flag for the user when they pick a monorepo path:

- **Sparse-checkout is automatic.** When `WIKI_SUBPATH` is non-empty, the Render/Docker `GitWikiSource` clones with `--filter=blob:none --sparse` and runs `git sparse-checkout set <subpath>`. For a 5 GB monorepo with a 50 MB wiki, that drops disk usage from ~5 GB to ~50 MB plus pack overhead. If you upgrade an *existing* non-sparse deployment, the init logic detects the missing sparse config and applies it — but the existing `.git/objects` still has all the blobs from the original clone, so you only see savings in the working tree. For full savings on an upgrade, wipe the disk (delete the Render disk or `docker volume rm wiki-mcp-{slug}-data`) and let the next boot re-clone sparsely.
- **Changing `WIKI_SUBPATH` requires a wipe.** Sparse-checkout is initialized on the first sparse-enabled boot and the configured path persists in `.git/info/sparse-checkout`. Changing the env var later won't re-trigger reconfiguration — to switch subpaths, delete `/var/data/wiki-repo` (or the Docker volume) and restart.
- **PAT scope.** Fine-grained GitHub PATs are repo-level minimum — the `WIKI_GIT_TOKEN` will have Contents:R/W on the entire monorepo, not just the wiki section. Treat with appropriate care; rotate after any handoff.
- **Tree truncation (Workers only).** GitHub's `/git/trees/?recursive=1` truncates at ~100k entries. The cron worker logs a warning if it hits this but doesn't fall back. Only matters for monorepos with >100k files total; the wiki section itself can be small.
- **Multiple wikis.** If the monorepo has more than one wiki (e.g. eng + product), run `/wiki-to-mcp` once per wiki with distinct slugs and subpaths. They deploy and authenticate independently.
- **Subpath normalization.** Trailing/leading slashes on `WIKI_SUBPATH` are normalized at config-load time, so `"apps/wiki"`, `"apps/wiki/"`, and `"/apps/wiki/"` all work. Multi-level subpaths like `"apps/docs/content/wiki"` are supported.
- **Write traversal guard still applies.** A malicious or buggy tool call with `path = "../../some-other-app/secrets.env"` is rejected at `resolveWikiPath` before any disk or GitHub API touch. Writes can never escape the wiki subpath into sibling apps.

## Notes on the Two Backend Code Paths

- **Render + Docker** share the same `src/wiki.ts` (the `simple-git` based one from `wiki-mcp-server/`). They share `src/index.ts` (Express + StreamableHTTPServerTransport). The only deltas are `Dockerfile`/`render.yaml`/`docker-compose.yml`.

- **Workers** is a different code path entirely:
  - `src/index.ts` is the Workers `fetch` handler, not Express.
  - Wiki state lives in R2; a separate `cron-worker.ts` syncs from GitHub.
  - Writes go through the GitHub Contents API (REST), not `git push`.
  - The MCP runtime uses Cloudflare's Workers MCP support (currently `agents` SDK / `workers-mcp`).

Be honest with the user: the Render/Docker paths are battle-tested by `wiki-mcp-server/`. The Workers path is supported but newer — flag it as such during the interview.
