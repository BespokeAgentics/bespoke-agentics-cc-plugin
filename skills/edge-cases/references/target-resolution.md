# Target resolution

`scripts/resolve_target.py` decides what is being analyzed, so the same input resolves the same way
every run. Stdlib only, read-only.

```bash
python3 {SKILL_DIR}/scripts/resolve_target.py [<target>] [--target auto|feature|plan|changes] [--base <ref>] \
        --repo {PROJECT_DIR} [--exclude <path> ...]
```

## The skill's own output is invisible

Every git query the script makes (status, untracked files, diffs, the symbol search, fingerprints)
excludes `.edge-cases/` and `reviews/edge-cases/`, plus every `--exclude` path. Pass the custom
output directory when `--out` is used, and `wiki` when a vault exists. Without the exclusions, one
run's report would make the next run's clean tree look dirty (rule 1), show up as a "changed file" in
the change set, and alter the fingerprint on every run, so resume could never match. Pre-flight also
writes `.edge-cases/.gitignore` containing `*`, so the work directory stays out of the user's own
`git status`.

## Detection order (`--target auto`)

The first rule that matches wins.

| # | Input | Resolves to |
| --- | --- | --- |
| 1 | nothing, working tree dirty | **changes** · `uncommitted` |
| 2 | nothing, clean, current branch ahead of its base | **changes** · `branch` |
| 3 | nothing, otherwise | **ask** — `candidates` lists recent plan documents and recent commits |
| 4 | `uncommitted`, `staged`, `branch` | **changes** with that scope |
| 5 | an existing path with a document extension (`.md .markdown .txt .rst .adoc .pdf`) | **plan** |
| 6 | any other existing path (source file or directory) | **feature**, `built: true` |
| 7 | `A..B` or `A...B` where both sides resolve to commits | **changes** · `range` |
| 8 | one identifier-like token that is **both** a git ref and a symbol in tracked code | **ask** — both readings offered |
| 9 | one token naming the **current** branch | **changes** · `branch`: that branch vs its base, **including** uncommitted work |
| 10 | one token naming another branch (local or remote) | **changes** · `branch`: that branch's commits vs its merge-base (committed work only) |
| 11 | one token that resolves to a commit and is not a branch (sha, tag, `HEAD`, `HEAD~2`) | **changes** · `commit` |
| 12 | one identifier-like token found in tracked code | **feature**, `built: true`, `matches` lists hits |
| 13 | anything else (a description) | **feature**, `built: null` — settled in pre-flight step 2 |

The symbol search (rules 8 and 12) is `git grep -w` over tracked files, **excluding documents** (the
extensions in rule 5): a word that appears only in a plan is not a built feature. For a dotted or
scoped token (`Cart.applyCoupon`, `Foo::bar`) it searches the last segment. `HEAD`, `ORIG_HEAD`,
`FETCH_HEAD`, `MERGE_HEAD`, `@` and full or abbreviated hex shas are never treated as symbols.

`--target <kind>` skips detection. `--target changes` with no target means `uncommitted`.
`--target plan` requires an existing file.

`built: null` means the script cannot tell whether a described feature exists. Pre-flight step 2
must settle it: search for the description now (names, routes, UI labels). Found → `true`. Nothing →
`false`: the feature is analyzed as a brief, `GROUNDED` is false, current behavior is `N/A`, and
`prove` degrades to `deep`. Write the settled value into `target.json`. `check_cases.py` rejects a
feature target whose `built` is still `null`.

## Output

```json
{
  "kind": "plan | feature | changes | ask",
  "spec": "the normalized target (path, text, or git expression)",
  "slug": "kebab-case, stable across runs for the same target",
  "fingerprint": "sha1 of the target's current content",
  "reason": "one line: which rule matched and why",
  "built": true,
  "matches": ["src/coupons.js:14:export function applyCoupon(cart, code, now = new Date()) {", "..."],
  "changes": {
    "scope": "uncommitted | staged | branch | commit | range",
    "base": "<full sha, or the empty-tree sha for a root commit>",
    "head": "<sha> | WORKTREE | INDEX",
    "branch": "<name, branch scope only>",
    "dirty": false,
    "diff_cmd": "git diff <base> [<head>] -- . ':(exclude).edge-cases' ':(exclude)reviews/edge-cases'",
    "files": [
      {"path": "src/coupons.js", "status": "M", "added": 12, "deleted": 3, "binary": false}
    ],
    "totals": {"files": 1, "added": 12, "deleted": 3}
  },
  "candidates": [
    {"kind": "plan", "spec": "plans/gift-cards.md", "label": "plans/gift-cards.md (modified 2026-10-18)"},
    {"kind": "changes", "spec": "a1b2c3d", "label": "a1b2c3d feat: fixed-amount coupons"}
  ],
  "notes": ["anything the script could not determine"]
}
```

- `built` is present on every resolved target (`plan`, `feature`, `changes`), not on `ask`.
- `changes` appears only for changes targets, `matches` only for symbol hits, `candidates` only for
  `ask`.
- `diff_cmd` uses full shas and carries the exclusions, so it can be run as printed. Untracked files
  are not in it: read them directly; they are listed in `files` with status `?`.
- File `status` is git's letter (`M` `A` `D` `T`) plus `?` for untracked. Renames are reported as a
  delete and an add (`--no-renames`), which is enough to find the surface.

## Slugs

| Kind | Slug |
| --- | --- |
| plan, feature path | the last two path parts, without the extension: `plans/gift-cards.md` → `plans-gift-cards`, `src/coupons.js` → `src-coupons`. Two `plan.md` files in different folders do not share a work directory. |
| feature description | the first six words: `bulk CSV import of customer addresses` → `bulk-csv-import-of-customer-addresses` |
| changes | `changes-uncommitted`, `changes-staged`, `changes-branch-<branch>`, `changes-<sha7>`, `changes-<sha7>-<sha7>` |

## Fingerprint and resume

Pre-flight writes the script's output (with `built` settled) to `{WORK_DIR}/target.json` and the run
parameters to `{WORK_DIR}/run.json`. Smart resume trusts existing phase outputs **only if** the stored
fingerprint equals the current one **and** the run parameters match. Any of these makes the earlier
analysis stale, so the run is treated as `--force` and the reason is given in one line:

- a changed document, an edited file under a feature path, or a different diff;
- a different level, lens set, focus, or grounding.

This matters most for `uncommitted`, where the slug stays the same while the diff keeps changing.

| Kind | Fingerprint covers |
| --- | --- |
| plan | the document's bytes |
| feature (path) | the index entries and working-tree diff under the path, plus untracked files under it |
| feature (description) | the description text and `HEAD` |
| changes | the diff output, plus untracked file contents |

## Exit codes

- `0` — resolved. This includes `ask`, and an empty change set, which is reported with
  `totals.files: 0` and a note; the skill then stops and says there is nothing to analyze.
- `2` — bad arguments, a `--target plan` path that does not exist, or a changes target outside a git
  repository.
