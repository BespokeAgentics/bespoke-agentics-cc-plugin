// Dependency-free parser for the harness YAML subset.
// Supported: block mappings, block sequences ("- item"), flow sequences of scalars ("[a, b]"),
// flow mappings of scalars ("{ a: 1, b: x }"), quoted and unquoted scalars, comments, blank lines,
// null/true/false/numbers. Not supported (fails loudly): anchors, aliases, tags, multi-document,
// block scalars (| and >). Flow collections may nest ("{ a: [1, 2] }"). Keep harness files inside the subset.

export class YamlError extends Error {
  line: number;
  constructor(message: string, line: number) { super(`YAML line ${line}: ${message}`); this.line = line; }
}

interface Line { indent: number; text: string; no: number }

function stripComment(s: string): string {
  let inS = false, inD = false;
  for (let i = 0; i < s.length; i++) {
    const c = s[i];
    if (c === "'" && !inD) inS = !inS;
    else if (c === '"' && !inS) inD = !inD;
    else if (c === "#" && !inS && !inD && (i === 0 || /\s/.test(s[i - 1]))) return s.slice(0, i).trimEnd();
  }
  return s.trimEnd();
}

function scalar(raw: string, no: number): unknown {
  const s = raw.trim();
  if (s === "" || s === "~" || s === "null") return null;
  if (s === "true") return true;
  if (s === "false") return false;
  if (/^-?\d+$/.test(s)) return parseInt(s, 10);
  if (/^-?\d*\.\d+$/.test(s)) return parseFloat(s);
  if (s.startsWith('"')) {
    if (!s.endsWith('"') || s.length < 2) throw new YamlError("unterminated double quote", no);
    return JSON.parse(s);
  }
  if (s.startsWith("'")) {
    if (!s.endsWith("'") || s.length < 2) throw new YamlError("unterminated single quote", no);
    return s.slice(1, -1).replace(/''/g, "'");
  }
  if (s.startsWith("[")) return flowSeq(s, no);
  if (s.startsWith("{")) return flowMap(s, no);
  if (s.startsWith("&") || s.startsWith("*") || s.startsWith("!") || s.startsWith("|") || s.startsWith(">")) {
    throw new YamlError(`unsupported YAML feature in "${s}" (anchors, aliases, tags and block scalars are outside the harness subset)`, no);
  }
  return s;
}

function splitFlow(inner: string, no: number): string[] {
  const parts: string[] = [];
  let cur = "", inS = false, inD = false, depth = 0;
  for (const c of inner) {
    if (c === "'" && !inD) inS = !inS;
    else if (c === '"' && !inS) inD = !inD;
    if (!inS && !inD) {
      if (c === "[" || c === "{") depth++;
      else if (c === "]" || c === "}") depth--;
      if (depth < 0) throw new YamlError("unbalanced flow collection", no);
      if (c === "," && depth === 0) { parts.push(cur); cur = ""; continue; }
    }
    cur += c;
  }
  if (depth !== 0) throw new YamlError("unbalanced flow collection", no);
  if (cur.trim() !== "") parts.push(cur);
  return parts;
}

function flowSeq(s: string, no: number): unknown[] {
  if (!s.endsWith("]")) throw new YamlError("unterminated flow sequence", no);
  const inner = s.slice(1, -1).trim();
  if (inner === "") return [];
  return splitFlow(inner, no).map((p) => scalar(p, no));
}

function flowMap(s: string, no: number): Record<string, unknown> {
  if (!s.endsWith("}")) throw new YamlError("unterminated flow mapping", no);
  const inner = s.slice(1, -1).trim();
  const out: Record<string, unknown> = {};
  if (inner === "") return out;
  for (const part of splitFlow(inner, no)) {
    const entry = splitEntry(part.trim(), no);
    if (!entry) throw new YamlError(`flow mapping entry "${part.trim()}" has no key`, no);
    out[entry.name] = scalar(entry.rest, no);
  }
  return out;
}

/** Split "name: value" respecting quotes; returns null when the line is not a mapping entry. */
function splitEntry(text: string, no: number): { name: string; rest: string } | null {
  let inS = false, inD = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (c === "'" && !inD) inS = !inS;
    else if (c === '"' && !inS) inD = !inD;
    else if (c === ":" && !inS && !inD && (i === text.length - 1 || /\s/.test(text[i + 1]))) {
      let name = text.slice(0, i).trim();
      if ((name.startsWith('"') && name.endsWith('"')) || (name.startsWith("'") && name.endsWith("'"))) name = name.slice(1, -1);
      if (name === "") throw new YamlError("empty mapping key", no);
      return { name, rest: text.slice(i + 1).trim() };
    }
  }
  return null;
}

export function parseYaml(src: string): unknown {
  const lines: Line[] = [];
  src.split(/\r?\n/).forEach((raw, i) => {
    if (/^\s*\t/.test(raw)) throw new YamlError("tabs are not allowed for indentation", i + 1);
    const text = stripComment(raw);
    if (text.trim() === "") return;
    if (text.trim() === "---") return;
    lines.push({ indent: raw.length - raw.trimStart().length, text: text.trim(), no: i + 1 });
  });
  if (lines.length === 0) return null;
  const [value, next] = parseBlock(lines, 0, lines[0].indent);
  if (next !== lines.length) throw new YamlError("unexpected content", lines[next].no);
  return value;
}

function parseBlock(lines: Line[], i: number, indent: number): [unknown, number] {
  if (lines[i].text.startsWith("- ") || lines[i].text === "-") return parseSeq(lines, i, indent);
  return parseMap(lines, i, indent);
}

function parseSeq(lines: Line[], i: number, indent: number): [unknown[], number] {
  const out: unknown[] = [];
  while (i < lines.length && lines[i].indent === indent && (lines[i].text.startsWith("- ") || lines[i].text === "-")) {
    const body = lines[i].text === "-" ? "" : lines[i].text.slice(2).trim();
    const no = lines[i].no;
    if (body === "") {
      if (i + 1 < lines.length && lines[i + 1].indent > indent) { const [v, n] = parseBlock(lines, i + 1, lines[i + 1].indent); out.push(v); i = n; }
      else { out.push(null); i++; }
      continue;
    }
    const entry = splitEntry(body, no);
    if (entry && !body.startsWith("[") && !body.startsWith("{") && !body.startsWith('"') && !body.startsWith("'")) {
      // "- name: value" is an inline mapping whose further entries sit at indent + 2
      const childIndent = indent + 2;
      const synthetic: Line[] = [{ indent: childIndent, text: body, no }];
      let j = i + 1;
      while (j < lines.length && lines[j].indent > indent) { synthetic.push(lines[j]); j++; }
      const [v, n] = parseMap(synthetic, 0, childIndent);
      if (n !== synthetic.length) throw new YamlError("bad indentation inside sequence item", synthetic[n].no);
      out.push(v); i = j;
      continue;
    }
    out.push(scalar(body, no)); i++;
  }
  if (i < lines.length && lines[i].indent > indent) throw new YamlError("bad indentation", lines[i].no);
  return [out, i];
}

function parseMap(lines: Line[], i: number, indent: number): [Record<string, unknown>, number] {
  const out: Record<string, unknown> = {};
  while (i < lines.length && lines[i].indent === indent) {
    const { text, no } = lines[i];
    if (text.startsWith("- ")) throw new YamlError("sequence item where a mapping entry was expected", no);
    const entry = splitEntry(text, no);
    if (!entry) throw new YamlError(`expected "name: value", got "${text}"`, no);
    if (entry.name in out) throw new YamlError(`duplicate entry "${entry.name}"`, no);
    if (entry.rest === "") {
      if (i + 1 < lines.length && lines[i + 1].indent > indent) {
        const [v, n] = parseBlock(lines, i + 1, lines[i + 1].indent);
        out[entry.name] = v; i = n;
      } else { out[entry.name] = null; i++; }
    } else { out[entry.name] = scalar(entry.rest, no); i++; }
  }
  if (i < lines.length && lines[i].indent > indent) throw new YamlError("bad indentation", lines[i].no);
  return [out, i];
}

/** Minimal emitter for the same subset (used by bootstrap to write policy/graph files). */
export function toYaml(value: unknown, indent = 0): string {
  const pad = " ".repeat(indent);
  if (value === null || value === undefined) return "null";
  if (typeof value !== "object") return scalarOut(value);
  if (Array.isArray(value)) {
    if (value.length === 0) return "[]";
    if (value.every((v) => v === null || typeof v !== "object")) return `[${value.map(scalarOut).join(", ")}]`;
    return value.map((v) => `${pad}- ${toYaml(v, indent + 2).replace(/^\s+/, "")}`).join("\n");
  }
  const entries = Object.entries(value as Record<string, unknown>);
  if (entries.length === 0) return "{}";
  return entries.map(([k, v]) => {
    const isFlatList = Array.isArray(v) && (v.length === 0 || v.every((x) => x === null || typeof x !== "object"));
    if (v !== null && typeof v === "object" && !isFlatList) {
      if (!Array.isArray(v) && Object.keys(v as object).length === 0) return `${pad}${k}: {}`;
      return `${pad}${k}:\n${toYaml(v, indent + 2)}`;
    }
    return `${pad}${k}: ${toYaml(v, indent)}`;
  }).join("\n");
}

function scalarOut(v: unknown): string {
  if (v === null || v === undefined) return "null";
  if (typeof v === "boolean" || typeof v === "number") return String(v);
  const s = String(v);
  if (s === "" || /^[\s\-?:,\[\]{}#&*!|>'"%@`]/.test(s) || /[:#]\s|:$|\s$|^(true|false|null|~)$|^-?\d/.test(s)) return JSON.stringify(s);
  return s;
}
