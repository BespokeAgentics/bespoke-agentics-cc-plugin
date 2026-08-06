#!/usr/bin/env node
/**
 * type-ratchet — weak-typing ratchet guard.
 *
 * Counts weak-typing diagnostics across the codebase and compares the count
 * to a committed baseline. The count may only fall. New `any` fails the
 * gate; removed `any` is locked in with `--update`.
 *
 * Why a ratchet: a codebase with 300 existing `any` cannot flip a blocking
 * `no-explicit-any` rule on without red-walling every developer. A ratchet
 * is green on day one and blocks only the NEXT regression. Existing debt
 * shrinks over time; the baseline follows it down and never back up.
 *
 * Counting engine, auto-detected:
 *   1. Biome (preferred): runs `biome lint` with a generated audit config so
 *      the count is engine-consistent even where the project's own Biome
 *      config disables linting. Rules counted by default:
 *      suspicious/noExplicitAny, suspicious/noImplicitAnyLet,
 *      suspicious/noEvolvingTypes.
 *   2. Regex fallback (no Biome resolvable): counts `as any`, `: any`,
 *      `<any…>`, `any[]` textually. Cruder, but deterministic.
 *   The engine used is recorded in the baseline. A baseline made with one
 *   engine never compares against counts from the other (exit 2 instead).
 *
 * Commands:
 *   --init               Write a fresh baseline from the current counts.
 *   --update             Lower-only baseline refresh. Needs RATCHET_ALLOW_UPDATE=1.
 *   --baseline <path>    Baseline file (default: config/type-strength-baseline.json).
 *   --include-tests      With --init: count test files too (default: production only).
 *   --json               Print current counts as JSON to stdout and exit 0.
 *
 * Exit codes: 0 pass · 1 regression · 2 baseline problem · 3 count failure · 64 usage.
 * This guard never writes to source files. It has no --fix mode on purpose.
 */
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const DEFAULT_BASELINE = "config/type-strength-baseline.json";
const DEFAULT_RULES = [
  "suspicious/noExplicitAny",
  "suspicious/noImplicitAnyLet",
  "suspicious/noEvolvingTypes",
];
const BASE_GLOBS = [
  "**",
  "!**/node_modules/**",
  "!**/dist/**",
  "!**/build/**",
  "!**/out/**",
  "!**/coverage/**",
  "!**/vendor/**",
  "!**/drizzle/**",
  "!**/_generated/**",
  "!**/__generated__/**",
  "!**/generated/**",
  "!**/.next/**",
  "!**/storybook-static/**",
  "!**/*.min.js",
  "!**/*.d.ts",
];
const TEST_GLOBS = [
  "!**/__tests__/**",
  "!**/*.test.ts",
  "!**/*.test.tsx",
  "!**/*.spec.ts",
  "!**/*.spec.tsx",
  "!**/e2e/**",
];
const REGEX_INCLUDE = "\\.(ts|tsx)$";
const REGEX_EXCLUDE =
  "(^|/)(node_modules|dist|build|out|coverage|vendor|drizzle|_generated|__generated__|generated|\\.next|storybook-static)(/|$)|\\.d\\.ts$";
const REGEX_TEST_EXCLUDE = "(^|/)(__tests__|e2e)(/|$)|\\.(test|spec)\\.(ts|tsx)$";
const ANY_PATTERNS = [/(?<!\w)as\s+any\b/g, /:\s*any\b/g, /<\s*any\s*[,>[\]]/g, /\bany\[\]/g];

function usage(message) {
  process.stderr.write(
    `\n✘ ${message}\n\nUsage: type-ratchet.mjs [--init|--update] [--baseline <path>] [--include-tests] [--json]\n`,
  );
  process.exit(64);
}

function parseArgs(argv) {
  const opts = {
    init: false,
    update: false,
    json: false,
    includeTests: false,
    baseline: DEFAULT_BASELINE,
  };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--init") opts.init = true;
    else if (arg === "--update") opts.update = true;
    else if (arg === "--json") opts.json = true;
    else if (arg === "--include-tests") opts.includeTests = true;
    else if (arg === "--baseline") {
      i += 1;
      if (!argv[i]) usage("--baseline needs a path");
      opts.baseline = argv[i];
    } else usage(`unknown argument ${arg}`);
  }
  if (opts.init && opts.update) usage("--init and --update are mutually exclusive");
  return opts;
}

function findBiome() {
  if (process.env.BIOME_BIN && fs.existsSync(process.env.BIOME_BIN)) return process.env.BIOME_BIN;
  let dir = process.cwd();
  for (;;) {
    const bin = path.join(dir, "node_modules", ".bin", "biome");
    if (fs.existsSync(bin)) return bin;
    const parent = path.dirname(dir);
    if (parent === dir) return null;
    dir = parent;
  }
}

function biomeVersion(bin) {
  try {
    return execFileSync(bin, ["--version"], { encoding: "utf8" }).trim();
  } catch {
    return "unknown";
  }
}

function shortCommit() {
  try {
    return execFileSync("git", ["rev-parse", "--short", "HEAD"], { encoding: "utf8" }).trim();
  } catch {
    return "unknown";
  }
}

function trackedFiles() {
  const out = execFileSync("git", ["ls-files", "-z"], {
    encoding: "utf8",
    maxBuffer: 64 * 1024 * 1024,
  });
  return out.split("\0").filter(Boolean);
}

/** Build the throwaway Biome audit config from policy and run one lint pass. */
function countWithBiome(bin, policy) {
  const rules = {};
  for (const rule of policy.rules) {
    const [group, name] = rule.split("/");
    if (!group || !name) throw new Error(`malformed rule in policy: ${rule}`);
    rules[group] = rules[group] || {};
    rules[group][name] = "error";
  }
  const config = {
    files: { ignoreUnknown: true, includes: policy.globs },
    formatter: { enabled: false },
    linter: { enabled: true, rules: { recommended: false, ...rules } },
  };
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "type-ratchet-"));
  let stdout;
  try {
    fs.writeFileSync(path.join(tmp, "biome.json"), JSON.stringify(config));
    const args = [
      "lint",
      `--config-path=${tmp}`,
      "--reporter=json",
      "--max-diagnostics=none",
      ...policy.paths,
    ];
    try {
      stdout = execFileSync(bin, args, {
        encoding: "utf8",
        maxBuffer: 512 * 1024 * 1024,
        stdio: ["ignore", "pipe", "pipe"],
      });
    } catch (error) {
      // Biome exits nonzero when it finds diagnostics — that IS the data.
      if (typeof error.stdout !== "string" || error.stdout.length === 0) {
        throw new Error(`biome lint failed: ${error.stderr || error.message}`);
      }
      stdout = error.stdout;
    }
  } finally {
    fs.rmSync(tmp, { recursive: true, force: true });
  }
  let parsed;
  try {
    parsed = JSON.parse(stdout);
  } catch {
    throw new Error("could not parse biome --reporter=json output");
  }
  const wanted = new Map(policy.rules.map((r) => [`lint/${r}`, r]));
  const byRule = Object.fromEntries(policy.rules.map((r) => [r, 0]));
  const files = {};
  for (const diagnostic of parsed.diagnostics || []) {
    const rule = wanted.get(diagnostic.category);
    if (!rule) continue;
    byRule[rule] += 1;
    const raw = diagnostic.location?.path?.file ?? diagnostic.location?.path ?? "unknown";
    const file =
      typeof raw === "string" ? path.relative(process.cwd(), path.resolve(raw)) : "unknown";
    files[file] = (files[file] || 0) + 1;
  }
  return { byRule, files };
}

/** Fallback when no Biome binary resolves: textual `any` census. */
function countWithRegex(policy) {
  const include = new RegExp(policy.regexInclude);
  const exclude = new RegExp(policy.regexExclude);
  const byRule = { "regex/any": 0 };
  const files = {};
  for (const file of trackedFiles()) {
    if (!include.test(file) || exclude.test(file)) continue;
    let source;
    try {
      source = fs.readFileSync(file, "utf8");
    } catch {
      continue;
    }
    let count = 0;
    for (const pattern of ANY_PATTERNS) {
      pattern.lastIndex = 0;
      const matches = source.match(pattern);
      if (matches) count += matches.length;
    }
    if (count > 0) {
      byRule["regex/any"] += count;
      files[file] = count;
    }
  }
  return { byRule, files };
}

function defaultPolicy(method, includeTests) {
  const globs = includeTests ? BASE_GLOBS : [...BASE_GLOBS, ...TEST_GLOBS];
  const regexExclude = includeTests ? REGEX_EXCLUDE : `${REGEX_EXCLUDE}|${REGEX_TEST_EXCLUDE}`;
  return {
    method,
    rules: method === "biome" ? DEFAULT_RULES : ["regex/any"],
    paths: ["."],
    globs,
    regexInclude: REGEX_INCLUDE,
    regexExclude,
  };
}

function count(policy, biomeBin) {
  if (policy.method === "biome") {
    if (!biomeBin) {
      throw new Error(
        "baseline was made with the biome engine but no biome binary resolves (checked BIOME_BIN and node_modules/.bin upward from cwd)",
      );
    }
    return countWithBiome(biomeBin, policy);
  }
  return countWithRegex(policy);
}

function writeBaseline(file, baseline) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, `${JSON.stringify(baseline, null, 2)}\n`);
}

function totals(byRule) {
  return Object.values(byRule).reduce((sum, n) => sum + n, 0);
}

const opts = parseArgs(process.argv.slice(2));
const biomeBin = findBiome();

// --init: measure once, record engine + policy + counts.
if (opts.init) {
  const method = biomeBin ? "biome" : "regex";
  const policy = defaultPolicy(method, opts.includeTests);
  let result;
  try {
    result = count(policy, biomeBin);
  } catch (error) {
    process.stderr.write(`\n✘ type-ratchet: ${error.message}\n`);
    process.exit(3);
  }
  writeBaseline(opts.baseline, {
    version: 1,
    generatedAt: new Date().toISOString(),
    generatedFrom: {
      commit: shortCommit(),
      method,
      biome: biomeBin ? biomeVersion(biomeBin) : null,
    },
    policy,
    counts: { total: totals(result.byRule), byRule: result.byRule },
    files: Object.fromEntries(Object.entries(result.files).sort((a, b) => b[1] - a[1])),
  });
  process.stderr.write(
    `type-ratchet: baseline written to ${opts.baseline} — engine ${method}, total ${totals(result.byRule)} across ${Object.keys(result.files).length} file(s).\n`,
  );
  process.exit(0);
}

let baseline;
try {
  baseline = JSON.parse(fs.readFileSync(opts.baseline, "utf8"));
} catch {
  process.stderr.write(
    `\n✘ type-ratchet: no readable baseline at ${opts.baseline}.\n\n  Fix: run \`node ${path.relative(process.cwd(), process.argv[1])} --init\` once and commit the baseline.\n\n`,
  );
  process.exit(2);
}
if (baseline.version !== 1 || !baseline.policy || !baseline.counts?.byRule) {
  process.stderr.write(`\n✘ type-ratchet: malformed baseline at ${opts.baseline}.\n`);
  process.exit(2);
}
const currentMethod = biomeBin ? "biome" : "regex";
if (baseline.policy.method === "biome" && currentMethod !== "biome") {
  process.stderr.write(
    `\n✘ type-ratchet: baseline uses the biome engine but no biome binary resolves here.\n  Counts from different engines are not comparable. Install Biome or re-init.\n`,
  );
  process.exit(2);
}

let result;
try {
  result = count(baseline.policy, biomeBin);
} catch (error) {
  process.stderr.write(`\n✘ type-ratchet: ${error.message}\n`);
  process.exit(3);
}

if (opts.json) {
  process.stdout.write(
    `${JSON.stringify({ total: totals(result.byRule), byRule: result.byRule }, null, 2)}\n`,
  );
  process.exit(0);
}

const regressions = [];
const reductions = [];
for (const rule of Object.keys({ ...baseline.counts.byRule, ...result.byRule })) {
  const before = baseline.counts.byRule[rule] || 0;
  const after = result.byRule[rule] || 0;
  if (after > before) regressions.push({ rule, before, after });
  else if (after < before) reductions.push({ rule, before, after });
}

// --update: lock reductions in. Refuse while any rule rose.
if (opts.update) {
  if (process.env.RATCHET_ALLOW_UPDATE !== "1") {
    process.stderr.write("\n✘ type-ratchet --update needs RATCHET_ALLOW_UPDATE=1.\n");
    process.exit(64);
  }
  if (regressions.length > 0) {
    process.stderr.write(
      "\n✘ type-ratchet --update refused: counts rose. Fix the regressions first; --update only records reductions.\n",
    );
    process.exit(1);
  }
  baseline.counts = { total: totals(result.byRule), byRule: result.byRule };
  baseline.files = Object.fromEntries(Object.entries(result.files).sort((a, b) => b[1] - a[1]));
  baseline.generatedAt = new Date().toISOString();
  baseline.generatedFrom = {
    commit: shortCommit(),
    method: baseline.policy.method,
    biome: biomeBin ? biomeVersion(biomeBin) : null,
  };
  writeBaseline(opts.baseline, baseline);
  process.stderr.write(`type-ratchet: baseline lowered to ${baseline.counts.total}.\n`);
  process.exit(0);
}

if (regressions.length === 0) {
  if (reductions.length > 0) {
    process.stderr.write(
      `type-ratchet: counts fell below the baseline. Lock it in: RATCHET_ALLOW_UPDATE=1 node ${path.relative(process.cwd(), process.argv[1])} --update\n`,
    );
  }
  process.exit(0);
}

// Regression report: name the rules that rose and the files that rose most.
const ruleRows = regressions
  .map(
    ({ rule, before, after }) =>
      `    ${rule.padEnd(36)} ${String(before).padStart(6)} → ${String(after).padEnd(6)} (+${after - before})`,
  )
  .join("\n");
const baselineFiles = baseline.files || {};
const risers = Object.entries(result.files)
  .map(([file, n]) => ({ file, n, delta: n - (baselineFiles[file] || 0) }))
  .filter((r) => r.delta > 0)
  .sort((a, b) => b.delta - a.delta)
  .slice(0, 20)
  .map(({ file, n, delta }) => `    ${file}  +${delta} (now ${n})`)
  .join("\n");
process.stderr.write(
  `\n✘ type-ratchet: weak-typing count rose above the committed baseline.\n\n` +
    `  Rule                                  baseline   current\n${ruleRows}\n\n` +
    `  Files that rose:\n${risers || "    (per-file attribution unavailable)"}\n\n` +
    `  Fix: replace \`any\` with a concrete type, or with \`unknown\` plus a type\n` +
    `  guard. Never widen the baseline to make this pass — the baseline records\n` +
    `  pre-existing debt only, and it only moves down.\n\n`,
);
process.exit(1);
