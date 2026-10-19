# Go-live checklist

Each item is graded against the collector's `go_live` section **and then verified by opening the
file or running the command**. Grades: 🟢 present and adequate · 🟡 present but stale, thin, or
unverified · 🔴 missing · ⚪ not applicable (say why). Every 🟡 and 🔴 produces one task, sized
S (< 2h) or M (half day). Anything larger is a Finish row, not a checklist item.

The checklist is written to `<out>/go-live-checklist.md` from
`assets/templates/go-live-checklist.md`. Items marked † depend on what "shipped" meant in Round 1.

## A · Repository hygiene

| Item | 🟢 means | How to verify |
|---|---|---|
| README | A stranger reaches a working install and sees the core path within ten minutes | Follow it in a clean directory. Time it. |
| LICENSE | Present, named in the manifest, matches the README | `cat LICENSE | head -3`; compare to `manifest.license` |
| CONTRIBUTING | Says how to set up, test, and submit; links the code of conduct | Open it |
| CHANGELOG | Has an entry for the shipping version, seeded from the ledger's Finish rows | Open it; the entry is written as part of this task if missing |
| SECURITY | A reporting contact and a response expectation | Open it |
| CODE_OF_CONDUCT | Present (Contributor Covenant or equivalent) † public repo | Open it |
| Issue templates | Bug and feature templates; a config that points support questions somewhere | `ls .github/ISSUE_TEMPLATE` |
| PR template | Checklist includes tests and docs | Open it |
| `.env.example` | Declares every variable `go_live.env.used_in_code` lists, with a comment each | Diff `used_but_undeclared` — must be empty |
| Secrets in history | No credentials in any commit | Run a scanner (`gitleaks detect`, `trufflehog git file://.`) if installed; otherwise 🟡 with the command named — never 🟢 by assumption |
| Default branch protection † | Protected on the host; CI required | `gh api repos/:owner/:repo/branches/<default>/protection` if `gh` is present; else 🟡 |
| Stale branches | Branches > 30 days stale listed for deletion or kept with a reason | From `branches`; the task lists them, the user deletes |
| Repository metadata † | Description, topics, homepage set on the host | `gh repo view --json description,repositoryTopics,homepageUrl`; else 🟡 |
| `.gitignore` | Build output, env files, editor debris excluded; nothing tracked that should not be | `git ls-files | grep -E '\.env$|node_modules|dist/'` — must be empty |

## B · Documentation

| Item | 🟢 means | Source |
|---|---|---|
| Quickstart | Install → first useful result, with the exact commands and expected output | Written if missing; verified by following it |
| Configuration reference | Every env var and config key, its default, and what happens when it is unset | `go_live.env.used_in_code` is the list |
| Architecture note | One page, at most one diagram, names the main components and the one data flow | Existing docs, or written from the Explore returns |
| **Known limitations** | One line per Disable row, in product terms | The ledger. Written as part of this task; never omitted when Disables exist |
| **Roadmap** | One line per Defer row | The ledger |
| API / CLI reference † | Generated or written for every public surface | `--help` output, OpenAPI, typedoc — whichever applies |
| Placeholder text | No "TODO", "TBD", "coming soon", lorem ipsum in any shipped doc | `go_live.readme.placeholder_text`; `grep -rn "TBD\|TODO\|coming soon" docs/ README.md` |

## C · Release mechanics

| Item | 🟢 means | How to verify |
|---|---|---|
| Version | One version, consistent across every manifest and the CHANGELOG | `grep -rn '"version"'` across manifests |
| Tag + release notes procedure | Written down; release notes drafted from the CHANGELOG entry | The plan includes the exact commands |
| CI green on default branch † | Latest run passed | `gh run list --branch <default> --limit 1` if available; else 🟡 |
| Tests | `tests.test_command` runs and passes locally | Run it. Record the count and duration. Zero tests is 🔴 with an honest note, not a task to write a test suite in a shipping week |
| Publish dry-run † | `npm publish --dry-run` / `uv build` / `cargo publish --dry-run` succeeds and the file list is right | Run it; inspect the included files for secrets and junk |
| Clean install † | Installing the published artefact (or cloning fresh) in an empty directory works | Do it in `$TMPDIR` |
| Deploy † | Hosted target reachable; health endpoint returns; env vars set | Only if "hosted" was selected; otherwise ⚪ |
| Rollback | One sentence on how to undo the release | Written if missing |

## D · Demo assets

| Item | 🟢 means | Note |
|---|---|---|
| Screenshot or recording of the core path | Exists, current, referenced from the README | If missing: the task points at `/bespoke-agentics:screencast-capture` and `/bespoke-agentics:highlight-reel`. Do not describe an asset that does not exist. |
| Social card / OG image † | Set on the repo or site | Only when outreach is in scope |

## Grading honesty

- A file you did not open is 🟡.
- A command you did not run is 🟡, with the command written in the task.
- "Present" is not a grade. A 40-byte README is 🟡.
- ⚪ requires a reason ("not hosted", "internal only — no CoC needed").
