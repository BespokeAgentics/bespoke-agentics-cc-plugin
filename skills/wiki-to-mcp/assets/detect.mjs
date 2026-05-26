#!/usr/bin/env node
/**
 * Wiki repo scanner for the wiki-to-mcp skill.
 *
 * Usage:
 *   node detect.mjs <wiki-root> [subpath]
 *
 * Emits a single-line JSON report to stdout. All logging is to stderr.
 *
 * No external deps — uses only Node 20 builtins so the skill works in any
 * environment where Node is available.
 */
import { promises as fs } from "node:fs";
import path from "node:path";

const ROOT = process.argv[2];
const SUBPATH = process.argv[3] ?? "";

if (!ROOT) {
  console.error("usage: detect.mjs <wiki-root> [subpath]");
  process.exit(2);
}

const SCAN_ROOT = path.resolve(ROOT, SUBPATH);

async function* walk(dir) {
  let entries;
  try {
    entries = await fs.readdir(dir, { withFileTypes: true });
  } catch {
    return;
  }
  for (const e of entries) {
    if (e.name.startsWith(".git")) continue;
    if (e.name === "node_modules") continue;
    const full = path.join(dir, e.name);
    if (e.isDirectory()) yield* walk(full);
    else if (e.isFile()) yield full;
  }
}

function parseFrontmatter(raw) {
  if (!raw.startsWith("---\n") && !raw.startsWith("---\r\n")) return null;
  const end = raw.indexOf("\n---", 4);
  if (end === -1) return null;
  const block = raw.slice(4, end);
  const fields = {};
  for (const line of block.split(/\r?\n/)) {
    const m = line.match(/^([A-Za-z0-9_-]+)\s*:\s*(.*)$/);
    if (m) fields[m[1]] = m[2].trim();
  }
  return fields;
}

function countLinks(text) {
  const obsidian = (text.match(/\[\[[^\]\n]+\]\]/g) || []).length;
  const mdRelative = (text.match(/\]\([^)]+\.md(?:#[^)]*)?\)/g) || []).length;
  return { obsidian, mdRelative };
}

async function readGitHeadBranch(root) {
  try {
    const head = await fs.readFile(path.join(root, ".git", "HEAD"), "utf8");
    const m = head.match(/ref:\s+refs\/heads\/(.+)/);
    return m ? m[1].trim() : null;
  } catch {
    return null;
  }
}

const report = {
  scan_root: SCAN_ROOT,
  default_branch: await readGitHeadBranch(ROOT),
  file_count: 0,
  markdown_files: 0,
  with_frontmatter: 0,
  frontmatter_fields: {},
  wikilinks: { obsidian: 0, markdown_relative: 0 },
  has_index_md: false,
  has_log_md: false,
  has_readme_md: false,
  directory_top_level: [],
  largest_files: [],
};

// Top-level dirs (one level deep under SCAN_ROOT)
try {
  const top = await fs.readdir(SCAN_ROOT, { withFileTypes: true });
  report.directory_top_level = top
    .filter((d) => d.isDirectory() && !d.name.startsWith("."))
    .map((d) => d.name)
    .sort();
} catch {}

const sizeQueue = [];

for await (const file of walk(SCAN_ROOT)) {
  report.file_count++;
  const rel = path.relative(SCAN_ROOT, file);
  const base = path.basename(file).toLowerCase();
  if (base === "_index.md") report.has_index_md = true;
  if (base === "_log.md") report.has_log_md = true;
  if (base === "readme.md") report.has_readme_md = true;

  if (!file.toLowerCase().endsWith(".md")) continue;
  report.markdown_files++;

  let raw;
  try {
    raw = await fs.readFile(file, "utf8");
  } catch {
    continue;
  }

  const fm = parseFrontmatter(raw);
  if (fm) {
    report.with_frontmatter++;
    for (const k of Object.keys(fm)) {
      report.frontmatter_fields[k] = (report.frontmatter_fields[k] || 0) + 1;
    }
  }

  const links = countLinks(raw);
  report.wikilinks.obsidian += links.obsidian;
  report.wikilinks.markdown_relative += links.mdRelative;

  sizeQueue.push({ path: rel, size: raw.length });
}

// Top frontmatter fields (sorted desc by count)
const fmRanked = Object.entries(report.frontmatter_fields)
  .sort((a, b) => b[1] - a[1])
  .slice(0, 12)
  .map(([field, count]) => ({ field, count }));
report.frontmatter_fields = fmRanked;

// Largest 5 markdown files (useful signal for whether a wiki is doc-heavy or note-heavy)
report.largest_files = sizeQueue
  .sort((a, b) => b.size - a.size)
  .slice(0, 5);

// Guess link style
const ob = report.wikilinks.obsidian;
const md = report.wikilinks.markdown_relative;
let guessed_style = "none";
if (ob > 0 || md > 0) {
  if (ob >= md * 3) guessed_style = "obsidian";
  else if (md >= ob * 3) guessed_style = "markdown";
  else guessed_style = "mixed";
}
report.guessed_style = guessed_style;

// Suggested filterable fields: top 5, exclude pure-metadata keys
const META = new Set(["created", "updated", "date", "modified", "sources"]);
report.suggested_filterable_fields = fmRanked
  .filter(({ field }) => !META.has(field.toLowerCase()))
  .slice(0, 5)
  .map(({ field }) => field);

process.stdout.write(JSON.stringify(report));
