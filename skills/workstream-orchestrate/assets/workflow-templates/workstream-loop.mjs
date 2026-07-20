// workstream-loop.mjs — the per-workstream code → validate → commit loop for one workstream.
//
// The `workstream-orchestrate` skill invokes this ONCE PER WORKSTREAM via:
//   Workflow({ scriptPath: '.../assets/workflow-templates/workstream-loop.mjs', args: { ... } })
//
// Nothing feature-specific is hardcoded here — everything specific travels in `args` and in the
// kickoff contract the agents READ (so slices stay verbatim, not summarized). Keep it generic:
// to change what a workstream does, change the contract + args, not this file.
//
// args = {
//   ws:          'WS-1',                       // the workstream id to run
//   planPath:    'docs/.../plan.md',           // authoritative plan (agents read the WS text verbatim)
//   contractPath:'.workstream/<slug>/kickoff-contract.md',  // the confirmed contract (agents read their slice)
//   gates:       ['bun run typecheck', ...],   // gate commands for this workstream
//   hardGates:   [{ id, statement, enforced_at, proof_method }],  // server-authoritative invariants
//   commitStyle: 'the repo /commit skill' | 'git commit (Conventional Commit)' | 'none',  // 'none' == --no-commit
//   attempts:    3,                            // max code→validate iterations before halt
//   models:      { code, validate, commit },   // optional per-phase model overrides (validate defaults to opus)
// }

export const meta = {
  name: 'workstream-loop',
  description: 'code → validate → commit for one workstream of a sequential, gated build',
  phases: [
    { title: 'code' },
    { title: 'validate' },
    { title: 'commit' },
  ],
}

const ws          = args?.ws ?? 'WS-0'
const PLAN        = args?.planPath ?? '(plan path not provided)'
const CONTRACT    = args?.contractPath ?? '(contract path not provided)'
const GATES       = Array.isArray(args?.gates) ? args.gates : []
const HARD_GATES  = Array.isArray(args?.hardGates) ? args.hardGates : []
const COMMIT      = args?.commitStyle ?? 'git commit (Conventional Commit; stage only this workstream\'s files)'
const ATTEMPTS    = args?.attempts ?? 3
const MODELS      = args?.models ?? {}

const gatesText = GATES.length
  ? GATES.map((g) => `- ${g}`).join('\n')
  : '- (none supplied — run the repo default typecheck/test/build discovered at pre-flight)'

const hardGatesText = HARD_GATES.length
  ? HARD_GATES.map((h) => `- ${h.id}: ${h.statement} — enforced_at ${h.enforced_at}; proof: ${h.proof_method}`).join('\n')
  : '- none declared for this workstream'

const IMPL = {
  type: 'object',
  properties: {
    files: { type: 'array', items: { type: 'string' } },
    summary: { type: 'string' },
    gateResults: { type: 'string' },
    hardGateReadiness: { type: 'string' },
  },
  required: ['files', 'summary', 'gateResults'],
}
const VERDICT = {
  type: 'object',
  properties: {
    pass: { type: 'boolean' },
    findings: { type: 'array', items: { type: 'string' } },
    proofs: { type: 'array', items: { type: 'string' } },
    gateResults: { type: 'string' },
  },
  required: ['pass', 'findings'],
}
const COMMIT_SCHEMA = {
  type: 'object',
  properties: {
    hash: { type: 'string' },
    subject: { type: 'string' },
    postStatus: { type: 'string' },
  },
  required: ['hash', 'subject'],
}

// Build agent opts, only setting `model` when an override is supplied (else inherit the session model).
function opts(label, phaseName, schema, model) {
  const o = { label, phase: phaseName, schema }
  if (model) o.model = model
  return o
}

let passed = false
let attemptsUsed = 0
let commit = null
let files = []
let lastFindings = []

for (let attempt = 1; attempt <= ATTEMPTS && !passed; attempt++) {
  attemptsUsed = attempt

  const priorFindings = lastFindings.length
    ? `PRIOR VALIDATE FINDINGS (fix exactly these, verbatim):\n${lastFindings.map((f) => `- ${f}`).join('\n')}`
    : 'PRIOR VALIDATE FINDINGS: none — first attempt.'

  phase('code')
  const impl = await agent(
    `You implement ONE workstream of a sequential, gated build, in the shared working tree — NO worktree.\n` +
    `Read ${CONTRACT} and implement ONLY the ${ws} section (its scope, seams, guardrails, terminal gate). ` +
    `Read the plan at ${PLAN} for the authoritative workstream text. Follow the "code" packet + return contract ` +
    `in the skill's references/subagent-packets.md and the universal guardrails.\n` +
    `${priorFindings}\n` +
    `GATES — run these yourself before returning:\n${gatesText}\n` +
    `DECLARED HARD GATES — enforce each at its authoritative layer (server-side, not client CSS):\n${hardGatesText}\n` +
    `Own only ${ws}'s files; never touch pre-existing or unrelated changes. ` +
    `Return {files, summary, gateResults, hardGateReadiness}.`,
    opts(`code:${ws} a${attempt}`, 'code', IMPL, MODELS.code),
  )
  files = impl?.files ?? files

  phase('validate')
  const verdict = await agent(
    `You are an adversarial, READ-ONLY validator for ${ws}. Do NOT edit any file. Assume the implementer is wrong ` +
    `until the evidence says otherwise. Read ${CONTRACT} (the ${ws} section + guardrails). Run \`git diff\` for the ` +
    `change basis. Follow the "validate" packet in references/subagent-packets.md.\n` +
    `DO ALL:\n` +
    `1. Re-run the gates and report each pass/fail with the verbatim failure tail:\n${gatesText}\n` +
    `2. Diff the tree vs the contract's decisions + guardrails; flag every violation (wrong dir/naming, ` +
    `client-only enforcement, unrelated files staged, lockfile edits).\n` +
    `3. PROVE or REFUTE each hard gate at its authoritative layer — craft the adversarial input, exercise ` +
    `enforced_at DIRECTLY (a focused call/test, never a UI click), record the artifact. Client-side hiding is NOT ` +
    `enforcement.\nHARD GATES:\n${hardGatesText}\n` +
    `pass=false if ANY gate fails, ANY guardrail is violated, or ANY hard gate is refuted. ` +
    `Return {pass, findings, proofs, gateResults}.`,
    opts(`validate:${ws} a${attempt}`, 'validate', VERDICT, MODELS.validate ?? 'opus'),
  )

  if (verdict?.pass) {
    passed = true
    if (COMMIT !== 'none') {
      phase('commit')
      const fileList = files.length ? files.join(', ') : '(derive from `git status` — only this workstream\'s files)'
      commit = await agent(
        `Create ONE Conventional Commit for ${ws}. Stage ONLY ${ws}'s files — never \`git add -A\`, never sweep ` +
        `pre-existing or unrelated changes. Do NOT push or open a PR.\n` +
        `FILES TO STAGE (from the implementer + \`git status\`): ${fileList}\n` +
        `COMMIT FLOW: ${COMMIT}\n` +
        `Confirm \`git status\` afterward shows only the intended files were committed and pre-existing dirt ` +
        `survived. Return {hash, subject, postStatus}.`,
        opts(`commit:${ws}`, 'commit', COMMIT_SCHEMA, MODELS.commit),
      )
    }
  } else {
    lastFindings = verdict?.findings ?? ['validate returned no structured verdict — treat as fail']
    log(`${ws} attempt ${attempt} FAILED: ${lastFindings.join(' | ')}`)
  }
}

if (!passed) {
  log(`HALT at ${ws} after ${attemptsUsed} attempt(s) — surface findings to the human; do NOT commit.`)
} else if (commit) {
  log(`${ws} committed: ${commit.hash} — ${commit.subject}`)
}

return { ws, passed, attempts: attemptsUsed, commit, findings: passed ? [] : lastFindings }
