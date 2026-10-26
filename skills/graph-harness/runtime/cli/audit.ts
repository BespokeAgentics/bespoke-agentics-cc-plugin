#!/usr/bin/env node
// audit [--target <dir>] [--dir <harness>] [--markdown]
// Scores the project against the 12-question checklist. JSON (default) or markdown. Exit 0 always (it is a report).
import { parseArgs, str, emit } from "./args.ts";
import { audit } from "../core/audit.ts";

const a = parseArgs(process.argv.slice(2));
try {
  const r = audit(str(a, "target") ?? a.positional[0] ?? ".", str(a, "dir"));
  if (a.flags.markdown) {
    const icon = { pass: "🟢", partial: "🟡", fail: "🔴" };
    const lines = [`# Harness audit — ${r.target}`, "", `Score **${r.score} / ${r.max}** · level detected **L${r.level_detected}** · smallest next upgrade: ${r.smallest_next_upgrade}`, "", "| # | Question | Status | Evidence | Fix |", "|---|---|---|---|---|",
      ...r.items.map((i) => `| ${i.id} | ${i.question} | ${icon[i.status]} ${i.status} | ${i.evidence.replace(/\|/g, "/")} | ${i.fix.replace(/\|/g, "/")} |`)];
    process.stdout.write(lines.join("\n") + "\n"); process.exit(0);
  }
  emit(r, 0);
} catch (e) { emit({ ok: false, error: (e as Error).message }, 1); }
