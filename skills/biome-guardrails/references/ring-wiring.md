# Ring Wiring — Hooks and CI for the Ratchet Guards

Enforcement that runs in one place gets bypassed. Wire each guard into every
ring the project has: local git hooks (fast feedback, bypassable with
`--no-verify`) and CI (authoritative, not bypassable). The same script runs
in both rings, so behavior never differs by layer.

Both guards auto-detect their mode: with file arguments they check only
those files (hook usage); with no arguments they scan every tracked file
(CI usage).

## Git hooks

Detect the manager first, in this order:

1. `lefthook.yml` / `lefthook.yaml` → lefthook
2. `.husky/` directory → husky
3. `simple-git-hooks` key in package.json → simple-git-hooks
4. `git config core.hooksPath` set → custom hook directory
5. none → offer to add lefthook, or fall back to plain `.git/hooks` scripts

Put the file-size guard on **pre-commit** (it is per-file and fast). Put the
type ratchet on **pre-push** (it scans the whole repo; roughly a second on a
mid-size codebase, but keep commits snappy).

### lefthook

```yaml
pre-commit:
  jobs:
    - name: max-file-lines
      glob: "*.{ts,tsx,js,jsx}"
      run: node scripts/guards/max-file-lines.mjs {staged_files} || true  # remove `|| true` to block

pre-push:
  jobs:
    - name: type-ratchet
      run: node scripts/guards/type-ratchet.mjs || true  # remove `|| true` to block
```

### husky

```bash
# .husky/pre-commit
git diff --cached --name-only --diff-filter=ACMR -z | xargs -0 node scripts/guards/max-file-lines.mjs || true

# .husky/pre-push
node scripts/guards/type-ratchet.mjs || true
```

## CI

Run both guards bare (repo mode) as a step that can fail the build.

### GitHub Actions

```yaml
- name: Quality ratchets (types · file size)
  run: |
    node scripts/guards/type-ratchet.mjs
    node scripts/guards/max-file-lines.mjs
  continue-on-error: true   # remove to block
```

### Azure Pipelines

```yaml
- script: |
    node scripts/guards/type-ratchet.mjs
    node scripts/guards/max-file-lines.mjs
  displayName: "Quality ratchets (types · file size)"
  continueOnError: true   # remove to block
```

If the repo already has a "repo guards" or aggregate lint step, extend that
step instead of adding a new one — one place to read, one place to flip.

## Warn → block graduation

Land warn-first when the team was not consulted or a refactor is in flight:
keep the `|| true` / `continue-on-error` markers. Flip to blocking by
deleting the markers — nothing else changes.

A ratchet with a committed, accurate baseline is green on day one, so it can
graduate immediately in most repos. The warn phase exists for the humans,
not the tool: it gives the team a window to see the messages before red is
possible.

Record the current phase wherever the repo documents its gates
(CONTRIBUTING or equivalent), with the flip procedure. An undocumented
warn-only gate stays warn-only forever.

## Protect the baselines

The guards refuse to raise a baseline, but nothing stops a hand-edit of the
JSON. Two cheap defenses:

1. If the project uses the config-protection Claude hook from this skill
   (`templates/protect-config-hook.sh`), add the two baseline paths to its
   protected list.
2. In CI, compare the committed baseline against trunk before running the
   guard — fail if any count rose:
   ```bash
   git show origin/main:config/type-strength-baseline.json > /tmp/trunk-baseline.json 2>/dev/null \
     && node -e "
       const trunk = require('/tmp/trunk-baseline.json').counts.byRule;
       const local = require('./config/type-strength-baseline.json').counts.byRule;
       const raised = Object.keys(local).filter(r => (local[r] ?? 0) > (trunk[r] ?? 0));
       if (raised.length) { console.error('baseline raised for: ' + raised.join(', ')); process.exit(1); }
     " \
     || true   # trunk has no baseline yet — first landing
   ```
   Use the repo's real default branch in place of `main`.
