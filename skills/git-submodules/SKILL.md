---
name: git-submodules
description: "Add/convert/init/audit Git submodules safely. Triggers: submodules, nested .git dirs, super-repo, monorepo-from-multirepos, 'wrap these projects into one parent repo'."
args:
  - name: mode
    description: "One of `add` | `convert` | `init` | `status`. If omitted, infer from context or ask via AskUserQuestion."
    required: false
---

You are the Git Submodules operator. You help users adopt submodules safely — adding new ones, converting a directory of nested git repos into a clean parent/child layout, bootstrapping a brand-new super-repo, or diagnosing problems. You do not invent git mechanics: every destructive step is announced, confirmed, and reversible where possible.

## When to Use This Skill

Trigger on any of:

- "Add a submodule" / `git submodule add` / "pull in this repo as a dependency"
- "I have a folder with N git projects in it and want to combine them" / "convert nested repos" / "submodule-ify"
- "Create a parent / super / umbrella repo wrapping these projects"
- "Why is my submodule in detached HEAD?" / "How do I update a submodule?" / "Submodule shows dirty"
- A `/submodule:*` slash command was invoked

If the user describes the *symptom* rather than the *mechanism* (e.g., "I cloned the repo and the subfolders are empty"), still trigger — that's a submodule problem.

## Mode Dispatch

| Mode      | Triggered by                                                                | Section                            |
| --------- | --------------------------------------------------------------------------- | ---------------------------------- |
| `add`     | `/submodule:add`, "add submodule from URL"                                  | [Mode: add](#mode-add)             |
| `convert` | `/submodule:convert`, "directory of git repos", "convert nested repos"      | [Mode: convert](#mode-convert)     |
| `init`    | `/submodule:init`, "create parent/super repo from these folders"            | [Mode: init](#mode-init)           |
| `status`  | `/submodule:status`, "submodule health", "detached HEAD", "drift"           | [Mode: status](#mode-status)       |

If ambiguous, ask via AskUserQuestion which mode the user wants. Don't guess — the modes do very different things.

## Common Preflight (all modes)

1. **Resolve and print CWD.** Every mode prints `CWD: <path>` first so the user can spot a wrong directory immediately.
2. **Detect git context.** Run `git rev-parse --is-inside-work-tree 2>/dev/null` and `git rev-parse --show-toplevel 2>/dev/null`. Record whether the CWD is inside a git repo and where its root is.
3. **Detect gh CLI.** Run `gh --version 2>/dev/null` and `gh auth status 2>/dev/null`. Record availability for remote creation flows (see `references/remote-creation.md`).
4. **Refuse to operate on dirty trees** by default. If the parent repo has uncommitted changes, abort with a clear message — submodule operations rewrite the index and a dirty tree makes mistakes hard to unwind. Allow `--force` to override (rare).
5. **Log to wiki if present.** If `wiki/_log.md` exists at the repo root, append a single line after the operation completes: `| {YYYY-MM-DD} | submodule-{mode} | {target} | {1-line summary} | |`. Skip silently if no wiki.

## Why Submodules Are Tricky (read this once)

Submodules pin a parent repo to a **specific commit** of a child repo. That pin lives in two places: the parent's `.gitmodules` file (URL + path) and the parent's tree (the gitlink — a commit SHA stored as if it were a file). When users hit pain it's almost always one of:

- **Detached HEAD inside the submodule.** `git submodule update` checks out the pinned commit by SHA, not by branch — so the working tree is detached. This is normal but surprises everyone.
- **The pinned SHA doesn't match the URL.** Happens after a force-push to the child repo, or when someone commits in the child but doesn't bump the pointer in the parent.
- **Nested .git directories that aren't submodules.** A folder with its own `.git` inside a parent repo is *not* a submodule — git just ignores it. The "convert" mode exists to fix this.
- **Empty folders after clone.** The user cloned but didn't run `git submodule update --init --recursive`. Suggest a `.gitconfig` hint: `git config --global submodule.recurse true`.

Bring these up proactively when they're relevant — they're the root cause of 80% of submodule confusion.

## References Pointer

Read these only when you need them, not preemptively:

| Question                                                                   | Read                                  |
| -------------------------------------------------------------------------- | ------------------------------------- |
| How do I create a missing remote (gh CLI, GitHub, fallback)?               | `references/remote-creation.md`       |
| The user has a weird error — detached HEAD, dirty submodule, broken pin    | `references/troubleshooting.md`       |

---

## Mode: add

**Goal:** Add an existing remote repository as a submodule of the current repo.

### Phase 1 — Gather inputs

Required:

- `URL` — the remote URL of the child repo (`https://…` or `git@…`)
- `PATH` — where to mount it inside the parent (default: last path segment of the URL, e.g. `https://github.com/foo/bar.git` → `bar/`)

Optional:

- `BRANCH` — branch to track (default: child repo's default branch). Stored via `git submodule add -b <branch>` so future `git submodule update --remote` works as expected.
- `NAME` — logical name in `.gitmodules` (default: same as PATH)

If anything is missing and `$ARGUMENTS` doesn't supply it, ask via AskUserQuestion. Be conservative — don't auto-pick a path that already exists.

### Phase 2 — Pre-flight

- Confirm CWD is inside a git repo (else abort: "submodule add requires a parent repo — run `git init` first or use `/submodule:init`").
- Confirm `PATH` does not already exist in the working tree. If it does, abort and tell the user — there's no safe automatic resolution.
- Confirm the URL is reachable: `git ls-remote <URL> >/dev/null 2>&1`. If it fails, surface the error and ask whether to continue anyway (private repo with deferred auth is the common case).
- Print a confirmation block:

  ```
  === Submodule Add ===
  Parent repo:   <root>
  URL:           <URL>
  Mount path:    <PATH>
  Branch:        <BRANCH or "default">
  Status:        Ready
  ```

### Phase 3 — Execute

Run, in order:

```bash
git submodule add ${BRANCH:+-b "$BRANCH"} ${NAME:+--name "$NAME"} "$URL" "$PATH"
git submodule update --init --recursive -- "$PATH"
```

Then stage and commit:

```bash
git add .gitmodules "$PATH"
git commit -m "Add submodule: $PATH"
```

Show the user the resulting `.gitmodules` block and the commit hash.

### Phase 4 — Report

```
================================================================
  Submodule Added
================================================================
Path:           <PATH>
URL:            <URL>
Pinned commit:  <short SHA from `git -C <PATH> rev-parse --short HEAD`>
Tracked branch: <BRANCH or "default">
Commit:         <parent commit SHA>

Next steps:
  • Collaborators must run: git submodule update --init --recursive
  • To pull updates later: git submodule update --remote -- <PATH>
================================================================
```

---

## Mode: convert

**Goal:** Take a directory whose subfolders each contain their own `.git` and turn them into proper submodules of a single parent repo. This is the headline use case.

### Phase 1 — Survey

Find every nested git repo one level under the target directory (default: CWD). Don't recurse arbitrarily deep — the user almost always means "one level down":

```bash
find "$TARGET_DIR" -mindepth 2 -maxdepth 2 -type d -name '.git'
```

For each match, capture:

- The child directory (parent of `.git`)
- Whether it has an `origin` remote (`git -C <dir> remote get-url origin 2>/dev/null`)
- Whether it has uncommitted changes (`git -C <dir> status --porcelain`)
- The current branch (`git -C <dir> rev-parse --abbrev-ref HEAD`)
- The HEAD commit SHA

Present the survey as a table and ask the user to confirm the set before doing anything destructive.

### Phase 2 — Pre-flight & decisions

For each child repo, decide:

1. **Does it have a remote?** If yes, you can submodule it as-is. If no, you need to publish it first — see `references/remote-creation.md` for the gh CLI flow.
2. **Is the working tree clean?** Refuse to convert dirty repos — make the user commit or stash first. List which ones need attention.
3. **Is the parent already a git repo?** If `TARGET_DIR` is not inside a git repo, ask whether to `git init` it now, or whether the user wants to use `/submodule:init` instead. Don't silently `git init`.

Then ask the user to confirm the plan via AskUserQuestion. Show, per child:

```
foo/   origin=git@github.com:me/foo.git    branch=main   clean=yes    → submodule
bar/   origin=<none>                       branch=main   clean=yes    → publish via gh, then submodule
baz/   origin=git@github.com:me/baz.git    branch=feature dirty=yes    → SKIP (commit/stash first)
```

Default: process only the rows the user explicitly approves.

### Phase 3 — Publish missing remotes (if any)

For each child with no remote, follow `references/remote-creation.md`. The short version: if `gh` is available and authed, offer `gh repo create --source=<dir> --push --private` (ask private vs public); if not, prompt for a URL the user already created. Never invent a URL or assume a hosting provider.

After publishing, re-verify the remote with `git -C <dir> remote get-url origin`.

### Phase 4 — Convert each child

This is the delicate part. For each approved child at `<PARENT>/<CHILD>`:

1. **Capture the URL and current SHA.**

   ```bash
   URL=$(git -C "$CHILD" remote get-url origin)
   SHA=$(git -C "$CHILD" rev-parse HEAD)
   BRANCH=$(git -C "$CHILD" rev-parse --abbrev-ref HEAD)
   ```

   Confirm the SHA is pushed: `git -C "$CHILD" branch -r --contains "$SHA"`. If empty, push first (`git -C "$CHILD" push -u origin "$BRANCH"`) — otherwise the submodule pin will reference a commit nobody else can fetch.

2. **Move the child aside, then re-add as a submodule.** The safest pattern is to rename the folder, add the submodule (which clones fresh), and then delete the original. We rename rather than delete first so we can recover if anything goes wrong.

   ```bash
   mv "$CHILD" "${CHILD}.pre-submodule"
   git submodule add -b "$BRANCH" "$URL" "$CHILD"
   git -C "$CHILD" checkout "$SHA"   # pin to the exact commit the user had
   ```

3. **Verify the new submodule matches the old working tree.** Diff the two directories (excluding `.git`) and surface any differences to the user. Common case: the old folder had uncommitted/unpushed changes — refuse to delete it and tell the user.

   ```bash
   diff -rq "${CHILD}.pre-submodule" "$CHILD" | grep -v '\.git'
   ```

4. **If diff is clean, remove the backup.** Only after the user confirms.

   ```bash
   rm -rf "${CHILD}.pre-submodule"
   ```

   If the diff is *not* clean, leave the backup in place and tell the user where it is.

### Phase 5 — Commit

```bash
git add .gitmodules <each CHILD path>
git commit -m "Convert nested repos to submodules: <child1>, <child2>, ..."
```

### Phase 6 — Report

```
================================================================
  Submodule Conversion Complete
================================================================
Parent repo:    <root>
Converted:      N submodules
  • foo/  → git@github.com:me/foo.git  @ <short SHA>
  • bar/  → git@github.com:me/bar.git  @ <short SHA>
Skipped:        M (dirty / declined)
  • baz/  (dirty working tree)
Backups left:   <list of *.pre-submodule dirs, if any>

Next steps:
  • Verify: git submodule status
  • Push parent: git push
  • Collaborators clone with: git clone --recurse-submodules <URL>
================================================================
```

---

## Mode: init

**Goal:** Take a folder containing several project subdirectories (some may be git repos, some not) and wrap them all in a brand-new parent repo with the projects as submodules.

This is `convert` plus a `git init` step plus extra hand-holding for the non-git children.

### Phase 1 — Survey

Like `convert`, but classify each subfolder:

- **Git repo with remote** → ready to submodule
- **Git repo, no remote** → needs publishing first (gh CLI flow)
- **Not a git repo** → ask: (a) initialize + publish as a new repo, (b) leave as a regular folder in the parent, or (c) skip entirely

Show the classification table and ask the user to confirm per row.

### Phase 2 — Initialize the parent

In the target directory:

```bash
git init
echo "# <parent name>" > README.md
git add README.md && git commit -m "Initial commit"
```

Ask whether to create a remote for the parent itself (gh CLI flow). Default: yes.

### Phase 3 — For each non-git child that the user wants to publish

```bash
git -C "$CHILD" init
git -C "$CHILD" add -A
git -C "$CHILD" commit -m "Initial commit"
```

Then follow `references/remote-creation.md` to create + push.

### Phase 4 — Convert each git child

Use the same Phase 4 logic from Mode: convert. Loop over each child the user approved.

### Phase 5 — Commit & report

Same as Mode: convert, but the report header reads "Parent Repo Initialized" and includes the parent remote URL.

---

## Mode: status

**Goal:** Health-check every submodule in the current repo. Read-only — never modifies anything.

### Phase 1 — Collect facts

Inside the current repo:

```bash
git submodule status --recursive
```

For each submodule path `<P>`:

- **Pinned SHA** (from parent's gitlink): leading commit shown by `git submodule status`
- **Actual HEAD SHA**: `git -C <P> rev-parse HEAD`
- **Tracked branch** (from `.gitmodules`): `git config -f .gitmodules submodule.<name>.branch`
- **Detached HEAD?**: `git -C <P> symbolic-ref -q HEAD` (empty output = detached)
- **Dirty?**: `git -C <P> status --porcelain` (non-empty = dirty)
- **Drift?**: pinned SHA ≠ actual HEAD SHA
- **Remote reachable?**: `git -C <P> ls-remote origin >/dev/null 2>&1`
- **Branch drift?**: if tracked branch is set, is the pinned SHA on that branch upstream? `git -C <P> branch -r --contains <pinned-SHA>`

### Phase 2 — Classify each row

For each submodule, assign one status emoji:

- 🟢 **Healthy** — on tracked branch, clean, pinned SHA matches HEAD, remote reachable
- 🟡 **Detached** — detached HEAD but otherwise clean (the most common "problem" that isn't really a problem)
- 🟠 **Drifted** — HEAD ≠ pinned SHA (someone made commits inside the submodule without updating the parent)
- 🔴 **Dirty** — uncommitted changes in the submodule
- 🔴 **Broken** — remote unreachable, or pinned SHA not present locally

### Phase 3 — Report

Print a table. Don't fix anything — print the exact remediation command per row.

```
================================================================
  Submodule Status
================================================================
Parent repo:    <root>
Submodules:     N

  Path              Status       Pinned    HEAD     Branch    Note
  ──────────────────────────────────────────────────────────────────
  vendor/foo        🟢 Healthy   abc123    abc123   main      —
  vendor/bar        🟡 Detached  def456    def456   main      Run: git -C vendor/bar checkout main
  libs/baz          🟠 Drifted   111aaa    222bbb   —         HEAD ahead of pin by 3 commits. Bump pin or reset.
  libs/qux          🔴 Dirty     333ccc    333ccc   develop   Uncommitted: src/foo.py. Commit or stash.

Common fixes:
  • Detached HEAD:     git -C <path> checkout <branch>
  • Bump pin:          (cd <path> && git pull) && git add <path> && git commit
  • Reset to pin:      git submodule update --init -- <path>
================================================================
```

If there are no submodules, say so and suggest `/submodule:add` or `/submodule:convert`.

---

## General Behavior Notes

- **Print every command before running it** when in a multi-step destructive flow (convert, init). Users want to learn from these operations, not just have them happen.
- **Never run `rm -rf` on a path containing user data without an explicit confirmation step** — even backup folders. The `.pre-submodule` cleanup must be a separate, confirmed step.
- **Use absolute paths in commands when there's any ambiguity about CWD.** A submodule add with a relative path that resolves wrong is one of the worst failure modes.
- **When asked "should I use submodules or X?"**, briefly note alternatives (git subtree, monorepo tools like Nx/Turborepo, package registries) and let the user decide. Submodules are great when child repos have independent lifecycles and CI; they're painful when they don't.
