#!/usr/bin/env python3
"""
scaffold_workspace.py — Emit the full Bun-workspace monorepo SKELETON in one command,
so the agent spends effort on porting components, not hand-writing ~11 config files.

It reads the bundled `assets/templates/`, substitutes <scope>/<name>, injects the right
per-`--library` dependency matrix, and writes:

  <out>/
    package.json  bunfig.toml  tsconfig.base.json  .gitignore
    packages/tokens/  package.json  src/.gitkeep        (token script fills src/)
    packages/ui/      package.json  tsconfig.json  svg-shim.d.ts
                      src/index.ts  src/lib/cx.ts  src/styles/index.css
                      src/components/.gitkeep
    apps/storybook/   package.json  tsconfig.json  vite.config.ts  svg-shim.d.ts
                      .storybook/main.ts  .storybook/preview.ts
                      src/pages/.gitkeep  src/fixtures/.gitkeep

After this, run `bun install` (idempotent), then `tokens_to_tailwind.py` (Phase 4) and
port components into the ready tree (Phase 5-6).

The skeleton is designed to `tsc --noEmit` clean while EMPTY — proving the config is
sound before any porting. Dependency-free (stdlib only); idempotent with `--force`.

Usage:
    python3 scaffold_workspace.py --out <dir> --name <scope> \
        [--analysis analysis.json] [--library untitled-ui-react|shadcn|custom] \
        [--framework react] [--templates DIR] [--force]
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_TEMPLATES = SCRIPT_DIR.parent / "assets" / "templates"


def sub(text: str, scope: str, name: str) -> str:
    return text.replace("<scope>", scope).replace("<name>", name)


def load_template(tdir: Path, fname: str) -> str:
    p = tdir / fname
    if not p.exists():
        raise SystemExit(f"ERROR: template not found: {p}")
    return p.read_text(encoding="utf-8")


# ---- per-library runtime dependency matrix (added to packages/ui deps) ----
def library_deps(library: str, source_uses_react_aria: bool) -> dict[str, str]:
    if library == "shadcn":
        return {"class-variance-authority": "^0.7.1"}
    if library == "untitled-ui-react" and source_uses_react_aria:
        # Full Untitled UI idiom: React Aria + its plugins.
        return {
            "react-aria-components": "^1.16.0",
            "tailwindcss-react-aria-components": "^2.0.0",
            "@untitledui/icons": "^1.0.0",
        }
    # custom, or adapted untitled-ui-react (plain-element source): clsx + tailwind-merge
    # are already in the template; nothing extra.
    return {}


CX_TS = '''import { clsx, type ClassValue } from "clsx";
import { extendTailwindMerge } from "tailwind-merge";

// `cx` is a conflict-aware class merger; extend it to know any custom text utilities
// your @theme defines (e.g. text-display-*) so tailwind-merge dedupes them correctly.
const twMerge = extendTailwindMerge({
  extend: { theme: { text: ["display-m", "display-l", "display-xl"] } },
});

export function cx(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

// `sortCx` is an identity helper (Untitled UI idiom) — it exists only so Tailwind
// IntelliSense sorts classes inside style objects. `cn` is a common alias for `cx`.
export function sortCx<T>(classes: T): T {
  return classes;
}
export const cn = cx;
'''

INDEX_TS = '''// Public surface of @<scope>/ui — re-export every library component here as you port it.
// Example: export { Button } from "./components/Button";
export {};
'''

PKG_TSCONFIG = {
    "extends": "../../tsconfig.base.json",
    "include": ["src/**/*", "svg-shim.d.ts"],
}
SB_TSCONFIG = {
    "extends": "../../tsconfig.base.json",
    "compilerOptions": {"types": ["node"]},
    "include": [".storybook/**/*", "src/**/*", "svg-shim.d.ts"],
}

GITIGNORE = "node_modules/\nstorybook-static/\ndist/\n*.log\n.DS_Store\n"


def write(path: Path, content: str, force: bool):
    if path.exists() and not force:
        print(f"  skip (exists): {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  wrote: {path}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Scaffold the Bun workspace skeleton.")
    ap.add_argument("--out", required=True, help="Workspace output directory")
    ap.add_argument("--name", required=True, help="Package scope (e.g. foundry -> @foundry/*)")
    ap.add_argument("--analysis", default=None, help="analysis.json (reads source_uses_react_aria)")
    ap.add_argument("--library", default="untitled-ui-react",
                    choices=["untitled-ui-react", "shadcn", "custom"])
    ap.add_argument("--framework", default="react")
    ap.add_argument("--templates", default=str(DEFAULT_TEMPLATES))
    ap.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = ap.parse_args()

    if args.framework != "react":
        print(f"NOTE: --framework {args.framework} — this scaffold emits the React skeleton; "
              f"adapt per references/targets/{args.framework}.md (storybook framework pkg, "
              f"component file extension, cx helper).")

    scope = re.sub(r"[^a-z0-9-]", "", args.name.lower()) or "app"
    name = f"{scope}-workspace"
    out = Path(args.out).expanduser()
    tdir = Path(args.templates).expanduser()

    source_rac = False
    if args.analysis:
        try:
            source_rac = bool(json.loads(Path(args.analysis).read_text()).get("source_uses_react_aria"))
        except Exception as e:
            print(f"  (could not read analysis.json: {e})")

    print(f"Scaffolding workspace @{scope}/* -> {out}  (library={args.library}, RAC={source_rac})")

    # ---- root ----
    write(out / "package.json", sub(load_template(tdir, "root-package.json"), scope, name), args.force)
    write(out / "bunfig.toml", load_template(tdir, "bunfig.toml"), args.force)
    write(out / "tsconfig.base.json", load_template(tdir, "tsconfig.base.json"), args.force)
    write(out / ".gitignore", GITIGNORE, args.force)

    # ---- packages/tokens ----
    write(out / "packages/tokens/package.json",
          sub(load_template(tdir, "tokens-package.json"), scope, name), args.force)
    write(out / "packages/tokens/src/.gitkeep",
          "# tokens.css, tailwind-theme.css, tokens.index.json land here (Phase 4)\n", args.force)

    # ---- packages/ui ----
    ui_pkg = json.loads(sub(load_template(tdir, "ui-package.json"), scope, name))
    # strip comment-* helper keys, inject the library dep matrix
    ui_pkg = {k: v for k, v in ui_pkg.items() if not k.startswith("comment-")}
    ui_pkg.setdefault("dependencies", {}).update(library_deps(args.library, source_rac))
    if args.library != "untitled-ui-react" or not source_rac:
        pass  # adapted/custom/shadcn: template deps (clsx+tailwind-merge) already correct
    write(out / "packages/ui/package.json", json.dumps(ui_pkg, indent=2) + "\n", args.force)
    write(out / "packages/ui/tsconfig.json", json.dumps(PKG_TSCONFIG, indent=2) + "\n", args.force)
    write(out / "packages/ui/svg-shim.d.ts", load_template(tdir, "svg-shim.d.ts"), args.force)
    write(out / "packages/ui/src/index.ts", sub(INDEX_TS, scope, name), args.force)
    write(out / "packages/ui/src/lib/cx.ts", CX_TS, args.force)
    write(out / "packages/ui/src/styles/index.css",
          sub(load_template(tdir, "ui-styles-index.css"), scope, name), args.force)
    write(out / "packages/ui/src/components/.gitkeep", "", args.force)

    # ---- apps/storybook ----
    write(out / "apps/storybook/package.json",
          sub(load_template(tdir, "storybook-package.json"), scope, name), args.force)
    write(out / "apps/storybook/tsconfig.json", json.dumps(SB_TSCONFIG, indent=2) + "\n", args.force)
    write(out / "apps/storybook/svg-shim.d.ts", load_template(tdir, "svg-shim.d.ts"), args.force)
    write(out / "apps/storybook/vite.config.ts", load_template(tdir, "vite.config.ts"), args.force)
    write(out / "apps/storybook/.storybook/main.ts",
          sub(load_template(tdir, "storybook-main.ts"), scope, name), args.force)
    write(out / "apps/storybook/.storybook/preview.ts",
          sub(load_template(tdir, "storybook-preview.ts"), scope, name), args.force)
    write(out / "apps/storybook/src/pages/.gitkeep",
          "# page-demo *.stories.tsx land here (Phase 6)\n", args.force)
    write(out / "apps/storybook/src/fixtures/.gitkeep",
          "# ported mock data lands here (Phase 6)\n", args.force)

    print("\nSkeleton written. Next:")
    print(f"  cd {out} && bun install")
    print(f"  python3 {SCRIPT_DIR/'tokens_to_tailwind.py'} <src>/tokens.css --out-dir packages/tokens/src")
    print("  # then copy the source tokens.css verbatim into packages/tokens/src/tokens.css")
    print("  bunx tsc --noEmit   # should be clean on the empty skeleton")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
