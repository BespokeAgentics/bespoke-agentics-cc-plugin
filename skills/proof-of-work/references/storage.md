# Storage & Publishing — where evidence lives and how reviewers see it

## The trade-off that decides everything

| | GitHub Actions artifacts v4 | S3-compatible bucket + presigned URLs |
|---|---|---|
| Inline images in PR comments | ❌ auth-gated zip downloads | ✅ presigned GET renders in markdown |
| Setup | zero | bucket + CI credentials |
| Cost | free (repo quota) | pennies (R2 has no egress fees) |
| Retention | `retention-days`, immutable, REST-addressable | your lifecycle policy |
| Best for | traces, HAR, bulky bundles | screenshots and diffs humans must *see* |

Recommended default: **both** — pixels to the bucket, bundles to artifacts. If the team refuses
new infra: artifacts-only and accept the click-through.

## Artifacts (v4 — v3 is deprecated)

```yaml
- uses: actions/upload-artifact@v4
  if: always()                      # evidence of failure is the most valuable evidence
  with:
    name: evidence-${{ github.run_id }}
    path: |
      evidence/
      test-results/**/trace.zip
    retention-days: 14
```

v4 artifacts are immutable and available via REST immediately (unique `artifact-id`) — agents in
later jobs can fetch and inspect them.

## Bucket upload + presigned URLs

```yaml
- name: Publish screenshots
  env:
    AWS_ACCESS_KEY_ID: ${{ secrets.EVIDENCE_AWS_KEY }}
    AWS_SECRET_ACCESS_KEY: ${{ secrets.EVIDENCE_AWS_SECRET }}
    # R2: also AWS_ENDPOINT_URL: ${{ secrets.R2_ENDPOINT }}
  run: |
    PREFIX="s3://$EVIDENCE_BUCKET/${{ github.repository }}/${{ github.run_id }}"
    aws s3 cp evidence/ "$PREFIX/" --recursive --exclude "*" --include "*.png"
    for f in evidence/*/*.png; do
      url=$(aws s3 presign "$PREFIX/${f#evidence/}" --expires-in 604800)   # 7 days
      echo "${f}|${url}" >> presigned.txt
    done
```

Presign expiry must exceed the PR review lifetime — 7 days default, regenerate on re-run.
Works identically against R2/MinIO (set the endpoint). Never grant the CI role more than
`PutObject` + presign on the evidence prefix.

## The evidence comment (create-or-update, never append-spam)

```yaml
- name: Evidence comment
  env: { GH_TOKEN: "${{ github.token }}" }
  run: |
    BODY=$(scripts/render-evidence-comment.sh presigned.txt evidence/*/manifest.json)
    EXISTING=$(gh pr comment list ${{ github.event.pull_request.number }} \
      --search "<!-- evidence-comment -->" --jq '.[0].id' 2>/dev/null || true)
    if [ -n "$EXISTING" ]; then gh pr comment --edit "$EXISTING" --body "$BODY"
    else gh pr comment ${{ github.event.pull_request.number }} --body "$BODY"; fi
```

Template the renderer fills (marker comment enables create-or-update):

```markdown
<!-- evidence-comment -->
## Evidence — commit `abc1234`

| Route | Before (main) | After (this PR) | Diff |
|-------|--------------|-----------------|------|
| /dashboard | ![before](presigned…) | ![after](presigned…) | 2.1% pixels |

**Checks**: console errors: ✅ 0 · text assertions: ✅ 3/3 · trace: [artifact](…)

**Reproduce**: `scripts/dev-stack.sh up review && scripts/evidence.sh`
```

## Baselines from main

```yaml
# .github/workflows/evidence-baseline.yml
on:
  push: { branches: [main] }
jobs:
  baseline:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - run: scripts/dev-stack.sh up baseline && scripts/evidence.sh baseline
      - run: aws s3 sync evidence/baseline/ "s3://$EVIDENCE_BUCKET/$GITHUB_REPOSITORY/baselines/" --delete
```

PR jobs pull `baselines/` before diffing. This keeps "before" always equal to current main —
no stale committed goldens, no "update the snapshots" ritual.

## Privacy & hygiene

- Screenshots capture whatever the app renders: run against **sim-data** seeds, never real user
  data, before pixels leave the machine.
- Bucket is private; presigned URLs are the only public surface, and they expire.
- `evidence/` is git-ignored (except committed baselines if that policy was chosen) — pixels in
  git history are forever.
- Lifecycle rule on the bucket: expire run-prefixed objects after 30–90 days; baselines exempt.
