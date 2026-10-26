// Dependency-free JSON Schema (draft 2020-12 subset) validator.
// Supported: type, properties, required, additionalProperties (bool | schema), enum, const,
// items, minItems, maxItems, minimum, maximum, minLength, maxLength, pattern, oneOf, anyOf,
// $ref to #/$defs/... within the same document. Anything else is ignored, so keep schemas
// inside this subset (the test suite asserts every shipped schema uses only these keywords).

export interface SchemaError { path: string; message: string }

export const SUPPORTED_KEYWORDS = new Set([
  "$schema", "$id", "title", "description", "type", "properties", "required", "additionalProperties",
  "enum", "const", "items", "minItems", "maxItems", "minimum", "maximum", "minLength", "maxLength",
  "pattern", "oneOf", "anyOf", "$ref", "$defs",
]);

type Json = unknown;

function typeOf(v: Json): string {
  if (v === null) return "null";
  if (Array.isArray(v)) return "array";
  if (typeof v === "number") return Number.isInteger(v) ? "integer" : "number";
  return typeof v;
}

function matchesType(v: Json, t: string): boolean {
  const actual = typeOf(v);
  if (t === "number") return actual === "number" || actual === "integer";
  return actual === t;
}

function resolveRef(root: any, ref: string): any {
  if (!ref.startsWith("#/")) throw new Error(`unsupported $ref: ${ref}`);
  let cur = root;
  for (const part of ref.slice(2).split("/")) {
    cur = cur?.[part.replace(/~1/g, "/").replace(/~0/g, "~")];
    if (cur === undefined) throw new Error(`unresolved $ref: ${ref}`);
  }
  return cur;
}

export function validate(schema: any, value: Json, root: any = schema, path = "$"): SchemaError[] {
  const errors: SchemaError[] = [];
  if (schema === true) return errors;
  if (schema === false) return [{ path, message: "schema is false" }];
  if (schema.$ref) {
    return validate(resolveRef(root, schema.$ref), value, root, path);
  }
  if (schema.type !== undefined) {
    const types = Array.isArray(schema.type) ? schema.type : [schema.type];
    if (!types.some((t: string) => matchesType(value, t))) {
      errors.push({ path, message: `expected ${types.join("|")}, got ${typeOf(value)}` });
      return errors;
    }
  }
  if (schema.const !== undefined && JSON.stringify(value) !== JSON.stringify(schema.const)) {
    errors.push({ path, message: `expected const ${JSON.stringify(schema.const)}` });
  }
  if (schema.enum && !schema.enum.some((e: Json) => JSON.stringify(e) === JSON.stringify(value))) {
    errors.push({ path, message: `expected one of ${schema.enum.map((e: Json) => JSON.stringify(e)).join(", ")}, got ${JSON.stringify(value)}` });
  }
  if (typeof value === "string") {
    if (schema.minLength !== undefined && value.length < schema.minLength) errors.push({ path, message: `shorter than ${schema.minLength}` });
    if (schema.maxLength !== undefined && value.length > schema.maxLength) errors.push({ path, message: `longer than ${schema.maxLength}` });
    if (schema.pattern && !new RegExp(schema.pattern).test(value)) errors.push({ path, message: `does not match ${schema.pattern}` });
  }
  if (typeof value === "number") {
    if (schema.minimum !== undefined && value < schema.minimum) errors.push({ path, message: `below minimum ${schema.minimum}` });
    if (schema.maximum !== undefined && value > schema.maximum) errors.push({ path, message: `above maximum ${schema.maximum}` });
  }
  if (Array.isArray(value)) {
    if (schema.minItems !== undefined && value.length < schema.minItems) errors.push({ path, message: `fewer than ${schema.minItems} items` });
    if (schema.maxItems !== undefined && value.length > schema.maxItems) errors.push({ path, message: `more than ${schema.maxItems} items` });
    if (schema.items) value.forEach((item, i) => errors.push(...validate(schema.items, item, root, `${path}[${i}]`)));
  }
  if (value && typeof value === "object" && !Array.isArray(value)) {
    const obj = value as Record<string, Json>;
    for (const name of schema.required ?? []) {
      if (!(name in obj)) errors.push({ path, message: `missing required property "${name}"` });
    }
    const props = schema.properties ?? {};
    for (const [name, sub] of Object.entries(props)) {
      if (name in obj) errors.push(...validate(sub, obj[name], root, `${path}.${name}`));
    }
    if (schema.additionalProperties !== undefined) {
      for (const name of Object.keys(obj)) {
        if (name in props) continue;
        if (schema.additionalProperties === false) errors.push({ path: `${path}.${name}`, message: "unexpected property" });
        else if (typeof schema.additionalProperties === "object") errors.push(...validate(schema.additionalProperties, obj[name], root, `${path}.${name}`));
      }
    }
  }
  if (schema.oneOf) {
    const passing = schema.oneOf.filter((s: any) => validate(s, value, root, path).length === 0).length;
    if (passing !== 1) errors.push({ path, message: `expected exactly one of ${schema.oneOf.length} alternatives to match, ${passing} did` });
  }
  if (schema.anyOf) {
    if (!schema.anyOf.some((s: any) => validate(s, value, root, path).length === 0)) errors.push({ path, message: "no anyOf alternative matched" });
  }
  return errors;
}

/** Walk a schema and return keywords the validator does not implement (so a schema never silently under-validates). */
export function unsupportedKeywords(schema: any, acc = new Set<string>()): string[] {
  if (!schema || typeof schema !== "object") return [...acc];
  if (Array.isArray(schema)) { schema.forEach((s) => unsupportedKeywords(s, acc)); return [...acc]; }
  for (const [k, v] of Object.entries(schema)) {
    if (!SUPPORTED_KEYWORDS.has(k)) acc.add(k);
    if (k === "properties" || k === "$defs") Object.values(v as object).forEach((s) => unsupportedKeywords(s, acc));
    else if (k === "items" || k === "additionalProperties") unsupportedKeywords(v, acc);
    else if (k === "oneOf" || k === "anyOf") (v as any[]).forEach((s) => unsupportedKeywords(s, acc));
  }
  return [...acc];
}

export function assertValid(schema: any, value: Json, what: string): void {
  const errs = validate(schema, value);
  if (errs.length) throw new Error(`${what} failed schema validation:\n` + errs.map((e) => `  ${e.path}: ${e.message}`).join("\n"));
}
