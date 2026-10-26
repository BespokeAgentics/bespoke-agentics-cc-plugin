#!/usr/bin/env node
// bootstrap --target <dir> --level 1|2|3 --task-class code|ui|research|data|mixed [--name <n>] [--force] [--dry-run]
// Scaffolds the harness into a repo at the chosen level. JSON manifest on stdout.
import { parseArgs, str, emit } from "./args.ts";
import { bootstrap } from "../core/bootstrap.ts";

const a = parseArgs(process.argv.slice(2));
try {
  const level = Number(str(a, "level") ?? "1");
  const task_class = str(a, "task-class") ?? "code";
  if (![1, 2, 3].includes(level)) throw new Error("--level must be 1, 2 or 3");
  if (!["code", "ui", "research", "data", "mixed"].includes(task_class)) throw new Error("--task-class must be code|ui|research|data|mixed");
  const res = bootstrap({ target: str(a, "target") ?? a.positional[0] ?? ".", level: level as 1 | 2 | 3, task_class: task_class as any, force: !!a.flags.force, dryRun: !!a.flags["dry-run"], name: str(a, "name") });
  emit({ ok: true, dry_run: !!a.flags["dry-run"], ...res }, 0);
} catch (e) { emit({ ok: false, error: (e as Error).message }, 1); }
