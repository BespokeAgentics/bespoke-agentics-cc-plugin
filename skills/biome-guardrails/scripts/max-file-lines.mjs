#!/usr/bin/env node
/**
 * max-file-lines — file-size ratchet guard.
 *
 * Caps the line count of source files. A new file must stay at or under the
 * cap. A file already over the cap at baseline time is recorded in the
 * baseline and may never grow. When an offender shrinks, `--update` locks
 * the smaller number in.
 *
 * Why: a file past ~1,500 lines stops getting reviewed as a whole. Every
 * 5,000-line file was once a 1,501-line file that no gate stopped.
 *
 * Two modes, auto-detected:
 *   ARGV mode (git hook): node max-file-lines.mjs <file...>
 *   Repo mode (CI/manual): node max-file-lines.mjs
 *     Scans every tracked file via `git ls-files -z`.
 *
 * Commands:
 *   --init              Write a fresh baseline of the current offenders.
 *   --update            Shrink-only baseline refresh. Needs RATCHET_ALLOW_UPDATE=1.
 *   --baseline <path>   Baseline file (default: config/file-size-baseline.json).
 *   --max <n>           Cap used by --init (default: 1500). Stored in the baseline.
 *
 * Exit codes: 0 pass · 1 violation · 2 baseline problem · 3 scan failure · 64 usage.
 * This guard never writes to source files. It has no --fix mode on purpose.
 */
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const DEFAULT_BASELINE = "config/file-size-baseline.json";
const DEFAULT_MAX = 1500;
const DEFAULT_INCLUDE = "\\.(ts|tsx|js|jsx)$";
const DEFAULT_EXCLUDE =
  "(^|/)(node_modules|dist|build|out|coverage|vendor|drizzle|_generated|__generated__|generated|\\.next|storybook-static)(/|$)|\\.d\\.ts$|\\.min\\.js$";

function usage(message) {
  process.stderr.write(
    `\n✘ ${message}\n\nUsage: max-file-lines.mjs [files...] [--init|--update] [--baseline <path>] [--max <n>]\n`,
  );
  process.exit(64);
}

function parseArgs(argv) {
  const opts = {
    init: false,
    update: false,
    baseline: DEFAULT_BASELINE,
    max: DEFAULT_MAX,
    files: [],
  };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--init") opts.init = true;
    else if (arg === "--update") opts.update = true;
    else if (arg === "--baseline") {
      i += 1;
      if (!argv[i]) usage("--baseline needs a path");
      opts.baseline = argv[i];
    } else if (arg === "--max") {
      i += 1;
      const n = Number(argv[i]);
      if (!Number.isInteger(n) || n < 1) usage("--max needs a positive integer");
      opts.max = n;
    } else if (arg.startsWith("--")) usage(`unknown flag ${arg}`);
    else opts.files.push(arg);
  }
  if (opts.init && opts.update) usage("--init and --update are mutually exclusive");
  return opts;
}

function trackedFiles() {
  const out = execFileSync("git", ["ls-files", "-z"], {
    encoding: "utf8",
    maxBuffer: 64 * 1024 * 1024,
  });
  return out.split("\0").filter(Boolean);
}

function countLines(file) {
  let source;
  try {
    source = fs.readFileSync(file, "utf8");
  } catch {
    return -1; // deleted in this commit, or unreadable — nothing to enforce
  }
  let lines = 0;
  for (let i = 0; i < source.length; i += 1) if (source[i] === "\n") lines += 1;
  return lines;
}

function shortCommit() {
  try {
    return execFileSync("git", ["rev-parse", "--short", "HEAD"], { encoding: "utf8" }).trim();
  } catch {
    return "unknown";
  }
}

function writeBaseline(file, baseline) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, `${JSON.stringify(baseline, null, 2)}\n`);
}

const opts = parseArgs(process.argv.slice(2));

// --init: record the cap and every current offender, then exit.
if (opts.init) {
  let all;
  try {
    all = trackedFiles();
  } catch (error) {
    process.stderr.write(`\n✘ git ls-files failed: ${error.message}\n`);
    process.exit(3);
  }
  const include = new RegExp(DEFAULT_INCLUDE);
  const exclude = new RegExp(DEFAULT_EXCLUDE);
  const offenders = {};
  for (const file of all) {
    if (!include.test(file) || exclude.test(file)) continue;
    const lines = countLines(file);
    if (lines > opts.max) offenders[file] = lines;
  }
  const sorted = Object.fromEntries(Object.entries(offenders).sort((a, b) => b[1] - a[1]));
  writeBaseline(opts.baseline, {
    version: 1,
    generatedAt: new Date().toISOString(),
    generatedFrom: { commit: shortCommit() },
    policy: { max: opts.max, include: DEFAULT_INCLUDE, exclude: DEFAULT_EXCLUDE },
    files: sorted,
  });
  process.stderr.write(
    `max-file-lines: baseline written to ${opts.baseline} — cap ${opts.max}, ${Object.keys(sorted).length} existing offender(s) frozen at their current size.\n`,
  );
  process.exit(0);
}

// Load the baseline. Enforcement is impossible without one.
let baseline;
try {
  baseline = JSON.parse(fs.readFileSync(opts.baseline, "utf8"));
} catch {
  process.stderr.write(
    `\n✘ max-file-lines: no readable baseline at ${opts.baseline}.\n\n  Fix: run \`node ${path.relative(process.cwd(), process.argv[1])} --init\` once and commit the baseline.\n\n`,
  );
  process.exit(2);
}
if (baseline.version !== 1 || !baseline.policy || typeof baseline.policy.max !== "number") {
  process.stderr.write(`\n✘ max-file-lines: malformed baseline at ${opts.baseline}.\n`);
  process.exit(2);
}

const max = baseline.policy.max;
const include = new RegExp(baseline.policy.include || DEFAULT_INCLUDE);
const exclude = new RegExp(baseline.policy.exclude || DEFAULT_EXCLUDE);
const known = baseline.files || {};

let candidates;
if (opts.files.length > 0) {
  candidates = opts.files.map((f) => path.relative(process.cwd(), path.resolve(f)));
} else {
  try {
    candidates = trackedFiles();
  } catch (error) {
    process.stderr.write(`\n✘ git ls-files failed: ${error.message}\n`);
    process.exit(3);
  }
}
candidates = candidates.filter((f) => include.test(f) && !exclude.test(f));

const violations = [];
const shrunk = [];
const current = {};
for (const file of candidates) {
  const lines = countLines(file);
  if (lines < 0) continue;
  current[file] = lines;
  const frozen = known[file];
  if (frozen !== undefined) {
    if (lines > frozen) {
      violations.push({ file, lines, limit: frozen, kind: "grew" });
    } else if (lines < frozen) {
      shrunk.push({ file, lines, frozen });
    }
  } else if (lines > max) {
    violations.push({ file, lines, limit: max, kind: "new" });
  }
}

// --update: lock in reductions. Refuse while any violation exists — a ratchet
// only turns one way.
if (opts.update) {
  if (process.env.RATCHET_ALLOW_UPDATE !== "1") {
    process.stderr.write("\n✘ max-file-lines --update needs RATCHET_ALLOW_UPDATE=1.\n");
    process.exit(64);
  }
  if (violations.length > 0) {
    process.stderr.write(
      "\n✘ max-file-lines --update refused: violations exist. Fix them first; --update only records reductions.\n",
    );
    process.exit(1);
  }
  const next = {};
  for (const [file, frozen] of Object.entries(known)) {
    const lines = current[file];
    if (lines === undefined) continue; // deleted or now out of scope — drop it
    if (lines > max) next[file] = Math.min(lines, frozen); // still an offender; freeze the smaller size
    // at or under the cap now — drop from the baseline entirely
  }
  baseline.files = Object.fromEntries(Object.entries(next).sort((a, b) => b[1] - a[1]));
  baseline.generatedAt = new Date().toISOString();
  baseline.generatedFrom = { commit: shortCommit() };
  writeBaseline(opts.baseline, baseline);
  const dropped = Object.keys(known).length - Object.keys(next).length;
  process.stderr.write(
    `max-file-lines: baseline updated — ${Object.keys(next).length} offender(s) remain, ${dropped} entry(ies) dropped.\n`,
  );
  process.exit(0);
}

if (violations.length === 0) {
  if (shrunk.length > 0) {
    process.stderr.write(
      `max-file-lines: ${shrunk.length} baselined file(s) shrank. Lock it in: RATCHET_ALLOW_UPDATE=1 node ${path.relative(process.cwd(), process.argv[1])} --update\n`,
    );
  }
  process.exit(0);
}

const report = violations
  .map(({ file, lines, limit, kind }) =>
    kind === "grew"
      ? `  ${file}:1  ${lines} lines (baselined offender frozen at ${limit} — it may not grow)`
      : `  ${file}:1  ${lines} lines (cap is ${max})`,
  )
  .join("\n");
process.stderr.write(
  `\n✘ max-file-lines: ${violations.length} file(s) over the cap:\n${report}\n\n` +
    `  A file this large stops getting reviewed as a whole. Split it along its\n` +
    `  natural seams (one domain, one module) instead of growing it.\n\n` +
    `  Fix: extract code into a new module, or split the file. Do not add the\n` +
    `  file to the baseline — the baseline records pre-existing debt only.\n\n`,
);
process.exit(1);
