# Remote Creation Flows

When converting nested repos or initializing a parent, some child repos won't have an `origin` remote. A submodule pin needs to point at a reachable URL, so we must publish those repos before adding them as submodules.

## Detection

Run once at the start of any flow that may need remote creation:

```bash
gh --version 2>/dev/null            # is gh installed?
gh auth status 2>/dev/null          # is gh authenticated?
```

Record three states:

- `gh-ready` — installed AND authenticated. Safe to use `gh repo create`.
- `gh-unauthed` — installed but not authenticated. Offer the user `gh auth login` (don't run it for them — it's interactive and may require browser).
- `gh-missing` — not installed. Fall back to manual URL prompt.

## Flow A: gh CLI available and authed

For each child repo that needs a remote, ask the user via AskUserQuestion:

1. **Visibility** — `private` (default) or `public`
2. **Owner** — default is the authenticated user; offer org options if known via `gh org list` (don't block if it fails)
3. **Name** — default to the child directory's basename; let the user override (GitHub names can't contain spaces; replace with `-`)

Then run, with CWD already inside the child repo:

```bash
gh repo create "<OWNER>/<NAME>" \
  --source=. \
  --remote=origin \
  --push \
  --${VISIBILITY}
```

`gh repo create --source=.` both creates the remote AND sets `origin` AND pushes the current branch. If the child has no commits yet, this will fail — make sure there's at least one commit first (the `init` mode handles this).

After it succeeds, verify:

```bash
git -C "$CHILD" remote get-url origin
```

## Flow B: gh installed but not authed

Tell the user:

```
gh is installed but not authenticated. To let me create remotes automatically:

    gh auth login

Re-run the command when finished, or pick "manual URL" below to provide
remote URLs you've already created.
```

Then offer two paths:

1. **Wait** — pause and let the user authenticate, then re-run.
2. **Manual** — fall through to Flow C.

## Flow C: gh missing or user declined

For each child repo that needs a remote, prompt the user for a URL they've already created (anywhere — GitHub, GitLab, Bitbucket, self-hosted, etc.). Validate the URL shape (`https://…` or `git@…:…`) but don't try to reach it yet — auth might be deferred.

Then, inside the child repo:

```bash
git -C "$CHILD" remote add origin "$URL"
git -C "$CHILD" push -u origin "$(git -C "$CHILD" rev-parse --abbrev-ref HEAD)"
```

If the push fails (auth, branch protection, empty repo on remote), surface the error verbatim. Don't try to repair it — let the user fix it and resume.

## Edge cases

- **Empty child repo** (no commits). Submodules can't pin to "nothing". The `init` mode handles this by making an initial commit before publishing. The `convert` mode should refuse and tell the user to commit first.
- **Detached HEAD in the child.** Can still push by SHA but it's confusing. Ask the user to check out a named branch first.
- **The remote already exists.** `gh repo create` will fail with a clear error. If the user actually wanted to point at the existing remote, drop into Flow C and ask for the URL.
- **Org with SSO enforcement.** `gh repo create` may succeed but subsequent `git push` may fail with an SSO error. Surface it and link the user to GitHub's SSO authorization page (`https://github.com/settings/tokens` is the entry point for classic tokens; for `gh auth login` they need to re-auth with `--scopes write:org`).
