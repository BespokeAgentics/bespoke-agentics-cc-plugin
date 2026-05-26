# Troubleshooting Submodules

A field guide for the most common submodule pain. Each entry is "symptom → diagnosis → fix". When a user reports something fuzzy, match it to one of these patterns first.

## "I cloned the repo and the subfolders are empty"

**Diagnosis.** The clone didn't initialize submodules. `.gitmodules` exists but the working trees were never checked out.

**Fix.**

```bash
git submodule update --init --recursive
```

**Prevention.** Suggest:

```bash
git config --global submodule.recurse true
# or, at clone time:
git clone --recurse-submodules <URL>
```

---

## "Submodule is in detached HEAD"

**Diagnosis.** Normal behavior. `git submodule update` checks out the **pinned SHA** by name, not a branch. The submodule's HEAD is the right commit; it's just not pointing at a branch ref.

**Fix.** Only an issue if the user intends to *make commits* inside the submodule. In that case:

```bash
git -C <submodule-path> checkout <branch>
# or, if .gitmodules has a `branch = X` entry:
git submodule update --remote -- <submodule-path>
```

After commits in the submodule, the user must update the parent's pin:

```bash
cd <parent>
git add <submodule-path>
git commit -m "Bump <submodule-path> to <short SHA>"
```

---

## "I committed in the submodule but the parent says it's dirty"

**Diagnosis.** The parent's gitlink still points at the old SHA. The "dirty" parent is correct — it's telling you the pin is out of date.

**Fix.** Either bump the pin or reset:

```bash
# bump the pin (keep your submodule commits)
cd <parent>
git add <submodule-path>
git commit -m "Bump <submodule-path>"

# OR reset the submodule back to the pinned commit (discard submodule commits)
git submodule update --init -- <submodule-path>
```

---

## "I deleted the folder but git still thinks it's a submodule"

**Diagnosis.** Submodules live in three places: `.gitmodules`, `.git/config`, and the parent's tree. Deleting the folder only removes one.

**Fix (the safe sequence).**

```bash
git submodule deinit -f -- <path>
git rm -f <path>                        # removes from tree AND .gitmodules
rm -rf ".git/modules/<path>"            # cleans the cached child .git dir
git commit -m "Remove submodule <path>"
```

---

## "Submodule add says 'already exists in the index'"

**Diagnosis.** A previous `git submodule add` was attempted, failed midway, and left entries in the index or `.git/modules`.

**Fix.**

```bash
git rm -f --cached <path>
rm -rf ".git/modules/<path>"
# .gitmodules may still have a stanza — remove it manually
git submodule add <URL> <path>
```

---

## "Submodule add fails with 'A git directory for X is found locally'"

**Diagnosis.** Same as above — leftover state in `.git/modules/<path>`.

**Fix.**

```bash
rm -rf ".git/modules/<path>"
git submodule add <URL> <path>
```

---

## "Pinned SHA isn't reachable from the remote"

**Diagnosis.** Someone committed in the submodule, bumped the parent's pin, but never pushed the submodule's commits. Now collaborators can't fetch the pinned SHA.

**Detection.**

```bash
cd <submodule-path>
PINNED=$(cd <parent> && git ls-tree HEAD <submodule-path> | awk '{print $3}')
git branch -r --contains "$PINNED"
# empty output → not pushed
```

**Fix.** The person who made the submodule commits must push them:

```bash
cd <submodule-path>
git push origin HEAD
```

If they're unreachable, the parent's pin must be rewound to a reachable SHA.

---

## "Nested .git folders aren't being treated as submodules"

**Diagnosis.** A folder with its own `.git` inside a parent repo is **not automatically a submodule**. Git sees it and ignores it. The parent's `git status` will show it as untracked or, worse, will quietly stop tracking changes inside it.

**Fix.** Run `/submodule:convert`.

---

## "I want to update all submodules to the latest of their tracked branches"

**Fix.**

```bash
git submodule update --remote --merge
# or, for a single one:
git submodule update --remote -- <path>
```

This advances each submodule to the tip of its tracked branch and merges into the local HEAD. The user must then commit the new pin in the parent.

---

## "submodule update is using the wrong URL"

**Diagnosis.** Someone edited `.gitmodules` but didn't sync `.git/config`. Git uses `.git/config` for the actual fetch URL.

**Fix.**

```bash
git submodule sync --recursive
git submodule update --init --recursive
```

---

## "I want to convert a submodule back to a regular directory"

**Diagnosis.** Sometimes the right call. Submodules add operational cost; if a child repo no longer has an independent lifecycle, fold it in.

**Fix.**

```bash
git submodule deinit -f -- <path>
git rm -f <path>
rm -rf ".git/modules/<path>"
# re-add as a regular directory:
cp -r <somewhere>/<path> <path>
rm -rf <path>/.git
git add <path>
git commit -m "Convert <path> from submodule to regular directory"
```

The history of the child is lost from the parent's perspective; if that matters, use `git subtree merge` instead.
