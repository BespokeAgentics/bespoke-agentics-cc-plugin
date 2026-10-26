// Tiny deterministic argv parser: --flag value | --flag=value | --bool | positional.
export interface Args { flags: Record<string, string | true>; positional: string[] }
export function parseArgs(argv: string[]): Args {
  const flags: Record<string, string | true> = {};
  const positional: string[] = [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith("--")) {
      const eq = a.indexOf("=");
      if (eq > 0) { flags[a.slice(2, eq)] = a.slice(eq + 1); continue; }
      const next = argv[i + 1];
      if (next !== undefined && !next.startsWith("--")) { flags[a.slice(2)] = next; i++; }
      else flags[a.slice(2)] = true;
    } else positional.push(a);
  }
  return { flags, positional };
}
export function str(a: Args, name: string, dflt?: string): string | undefined {
  const v = a.flags[name];
  return v === undefined ? dflt : v === true ? "" : v;
}
export function emit(obj: unknown, exitCode = 0): never {
  process.stdout.write(JSON.stringify(obj, null, 2) + "\n");
  process.exit(exitCode);
}
