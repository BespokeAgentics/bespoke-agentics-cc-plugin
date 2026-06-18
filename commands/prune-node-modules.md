---
name: "bespokeagentics:prune-node-modules"
description: "Reclaim disk space by finding and deleting stale node_modules directories. Scans a projects folder (default ~/Documents/Projects), flags every node_modules whose project has not been touched in N days (default 30 — by source-file edit OR git commit, ignoring node_modules/.git/build-output churn), and guides you through a dry-run review before any permanent deletion. Correctly handles monorepos, git worktrees, paths with spaces, and macOS iCloud snapshot accounting."
argument-hint: "[--dir <path>] [--days N] [--apply] [--trash] [--log <file>]"
allowed-tools: Bash, Read, AskUserQuestion
---

# Prune Stale node_modules

Wrap the bundled `prune-node-modules.sh` reaper to reclaim disk space safely.
It identifies `node_modules` belonging to projects that have gone dormant and
removes them — always **dry-run first, delete only after you confirm**. Deleted
deps are fully regenerable with one `npm`/`pnpm`/`yarn install`.

## Context

- Reaper (plugin): !`[ -x "${CLAUDE_PLUGIN_ROOT}/scripts/prune-node-modules.sh" ] && echo "${CLAUDE_PLUGIN_ROOT}/scripts/prune-node-modules.sh" || echo "(missing)"`
- Reaper (fallback): !`[ -x "$HOME/bin/prune-node-modules.sh" ] && echo "$HOME/bin/prune-node-modules.sh" || echo "(missing)"`
- Disk free now: !`df -h /System/Volumes/Data 2>/dev/null | awk '/disk/{print $4" free, "$5" used"}'`
- Requested args: `$ARGUMENTS`

## Arguments

Parse from `$ARGUMENTS` (all optional) and forward them verbatim to the script:

```
[--dir <path>] [--days N] [--apply] [--trash] [--log <file>]
```

- `--dir <path>` — root to scan. Default `~/Documents/Projects`. Pass `~/Documents` to sweep wider.
- `--days N` — staleness threshold in days. Default `30`.
- `--apply` — user intent to actually delete. Even when present, run the dry-run preview and confirm FIRST (see Process).
- `--trash` — route deletions to the Trash (recoverable) instead of `rm -rf`. Note: space is not freed until the Trash is emptied.
- `--log <file>` — append a deletion record. Default to `~/node_modules_pruned.log` when applying.

## Process

1. **Resolve the script.** Use `${CLAUDE_PLUGIN_ROOT}/scripts/prune-node-modules.sh` if executable;
   otherwise fall back to `~/bin/prune-node-modules.sh`. If neither exists, copy the bundled plugin
   script to `~/bin/`, `chmod +x` it, and proceed. Capture the resolved path as `$REAPER`.

2. **Dry-run preview (always).** Run `"$REAPER"` with the user's `--dir`/`--days`/`--trash` flags but
   **without** `--apply`, teeing to a temp report (e.g. `~/node_modules_dryrun.txt`). The script
   defaults to dry-run, so nothing is deleted. The scan touches hundreds of directories — allow a
   generous timeout and, if it auto-backgrounds, poll the output file until the `SUMMARY` block appears.

3. **Summarize for the user.** From the report, present: total node_modules found, count stale vs.
   kept-active, the **space that would free**, the ~10 biggest deletions (size + last-activity date),
   and the list of projects being **kept** (so they can confirm nothing live is being cut).

4. **Confirm before deleting.** If `--apply` was NOT in `$ARGUMENTS`, use AskUserQuestion to offer:
   apply now / be more conservative (larger `--days`) / hold off. If `--apply` WAS passed, still show
   the preview summary and get a brief explicit confirmation before the destructive step — deletion is
   permanent (with `rm -rf`).

5. **Apply (on approval).** Re-run `"$REAPER" --apply --log <logfile>` plus the user's other flags.
   Capture before/after free space with `df -h /System/Volumes/Data`.

6. **Reconcile freed space (macOS/iCloud caveat).** If the scan root is under an iCloud-managed path
   (e.g. `~/Documents`), freed space is often held by APFS local Time Machine snapshots and shows as
   "purgeable" rather than free. Check `tmutil listlocalsnapshots /`; if snapshots are holding the
   deletions, offer to thin them (`tmutil thinlocalsnapshots / <bytes> 4`) to realize the space.
   Local snapshots are a transient cache — NOT the user's real Time Machine backups.

## Safety

- **Never delete without a dry-run + explicit confirmation**, even if `--apply` is passed.
- The "kept-active" list is the safety check — verify no project the user is actively working in
  appears in the delete set (and remember: even a wrong deletion just costs a reinstall).
- Refuse to operate if the resolved `--dir` is `$HOME` or `/` (the script enforces this too).
- Prefer `rm -rf` for immediate reclaim; suggest `--trash` only when the user is unsure.

## Output

- `~/node_modules_dryrun.txt` — the dry-run report (reviewable).
- `~/node_modules_pruned.log` — tab-separated record of every deletion (when applied).
- A final summary: node_modules removed, space freed, projects kept, and realized free-space delta.
