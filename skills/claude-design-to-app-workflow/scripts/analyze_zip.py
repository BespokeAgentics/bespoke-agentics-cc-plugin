#!/usr/bin/env python3
"""
analyze_zip.py — Deeply inspect a Claude (claude.ai) design-export zip and emit a
structured manifest the skill uses to drive code generation.

It is intentionally dependency-free (stdlib only) so it runs anywhere `python3`
exists. It does NOT assume the Foundry layout — it classifies whatever it finds.

Usage:
    python3 analyze_zip.py <path-to.zip | extracted-dir> [--out analysis.json] [--extract-to DIR]

What it does:
  1. Extracts the zip (or reads an already-extracted dir) into a work dir.
  2. Walks the tree and classifies every file into a role
     (tokens / primitives / composite / page / data / entry / asset /
      screenshot / html / style / config / unknown).
  3. Detects the SOURCE framework (react-jsx, react-tsx, vue, svelte, html).
  4. Extracts a COMPONENT INVENTORY from JS/JSX/TSX: component names + the
     destructured prop names and their literal defaults (so the generator can
     emit typed props and Storybook controls without re-deriving them).
  5. Extracts DESIGN TOKENS: every CSS custom property, grouped by the selector
     scope it was declared under (:root / [data-theme="dark"] / [data-theme="light"]
     / etc.), plus detected theme names and @import font URLs.
  6. Detects Tokens Studio / DTCG JSON token files if present.
  7. Prints a human-readable summary and writes analysis.json.

The manifest is a recommendation, not gospel — the generating model should read
the actual files for anything nuanced. This just removes the rote inventory work
every run would otherwise repeat.
"""
from __future__ import annotations
import argparse, json, os, re, sys, tempfile, zipfile
from pathlib import Path

# -----------------------------------------------------------------------------
# File-role classification
# -----------------------------------------------------------------------------

CODE_EXTS = {".jsx", ".tsx", ".js", ".ts", ".vue", ".svelte"}
STYLE_EXTS = {".css", ".scss", ".sass", ".less"}
IMG_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
VECTOR_EXTS = {".svg"}

# Substrings (checked against the lowercased path) that hint at a role.
PRIMITIVE_HINTS = ("primitive", "component", "/ui/", "atom", "element", "widget")
COMPOSITE_HINTS = ("shell", "layout", "nav", "sidebar", "topbar", "header", "footer",
                   "scaffold", "frame", "chrome", "drawer", "tweak", "panel")
PAGE_HINTS = ("/pages/", "/page/", "/routes/", "/views/", "/screens/", "/app/(")
DATA_HINTS = ("data", "mock", "fixture", "seed", "sample", "content", "store")
ENTRY_HINTS = ("app.", "main.", "index.", "root.", "router", "routes.")
TOKEN_HINTS = ("token", "theme", "variable", "design-token")


def classify(rel: str, ext: str, text: str | None) -> str:
    p = rel.lower()
    if ext in IMG_EXTS:
        return "screenshot" if ("screenshot" in p or "shot" in p or "/thumb" in p
                                or p.endswith(".thumbnail")) else "asset"
    if ext in VECTOR_EXTS or "/assets/" in p or "/icons/" in p or "/img/" in p:
        return "asset"
    if ext == ".html":
        return "html"
    if ext == ".json":
        if text and looks_like_token_json(text):
            return "tokens"
        return "config"
    if ext in STYLE_EXTS:
        # A stylesheet with many custom-property declarations IS the token sheet.
        if text and len(CSS_VAR_DECL.findall(text)) >= 8:
            return "tokens"
        if any(h in p for h in TOKEN_HINTS):
            return "tokens"
        return "style"
    if ext in CODE_EXTS:
        if any(h in p for h in PAGE_HINTS):
            return "page"
        if any(h in p for h in COMPOSITE_HINTS):
            return "composite"
        if any(h in p for h in PRIMITIVE_HINTS):
            return "primitives"
        if any(h in p for h in DATA_HINTS):
            return "data"
        if any(p.endswith(e) or ("/" + e) in p for e in ENTRY_HINTS):
            return "entry"
        return "code"
    return "unknown"


# -----------------------------------------------------------------------------
# Token (CSS custom property) extraction
# -----------------------------------------------------------------------------

CSS_VAR_DECL = re.compile(r"--([A-Za-z0-9][\w-]*)\s*:\s*([^;{}]+);")
# Selector blocks like  :root { ... }  or  [data-theme="light"] { ... }
SELECTOR_BLOCK = re.compile(r"([^{}]+)\{([^{}]*)\}", re.DOTALL)
FONT_IMPORT = re.compile(r"@import\s+url\(([^)]+)\)")
THEME_SELECTOR = re.compile(r'\[data-theme\s*=\s*["\']?([\w-]+)["\']?\]')


def extract_css_tokens(text: str) -> dict:
    """Return {scopes: {selector: {var: value}}, themes: [...], fonts: [...], count}."""
    scopes: dict[str, dict[str, str]] = {}
    for sel_raw, body in SELECTOR_BLOCK.findall(text):
        decls = CSS_VAR_DECL.findall(body)
        if not decls:
            continue
        sel = " ".join(sel_raw.split()).strip()
        bucket = scopes.setdefault(sel, {})
        for name, value in decls:
            bucket[name] = value.strip()
    themes = sorted(set(THEME_SELECTOR.findall(text)))
    fonts = [m.strip("\"'") for m in FONT_IMPORT.findall(text)]
    total = sum(len(v) for v in scopes.values())
    return {"scopes": scopes, "themes": themes, "fonts": fonts, "var_count": total}


def looks_like_token_json(text: str) -> bool:
    """Heuristic for Tokens Studio / DTCG token JSON."""
    head = text[:4000]
    return ('"value"' in head and ('"type"' in head or '"$type"' in head)) or \
           '"$themes"' in head or '"$metadata"' in head


# -----------------------------------------------------------------------------
# Component + prop extraction from JS / JSX / TSX
# -----------------------------------------------------------------------------

# function Foo(  |  const Foo = (  |  const Foo = function  |  const Foo = ({  |
# const Foo = forwardRef(  |  export function Foo(  |  export const Foo =
COMP_DEF = re.compile(
    r"(?:export\s+)?(?:default\s+)?function\s+([A-Z][A-Za-z0-9_]*)\s*\(([^)]*)\)"
    r"|(?:export\s+)?(?:default\s+)?const\s+([A-Z][A-Za-z0-9_]*)\s*=\s*"
    r"(?:React\.)?(?:memo\(|forwardRef\(|\()?\s*(?:function\s*)?\(?([^)=]*)\)?\s*=>"
)
# Object.assign(window, { A, B, C })  /  export { A, B }
WINDOW_EXPORT = re.compile(r"Object\.assign\(\s*window\s*,\s*\{([^}]*)\}", re.DOTALL)
NAMED_EXPORT = re.compile(r"export\s*\{([^}]*)\}")
# Destructured props:  ({ a, b='x', c=10, d=true, ...rest })
def parse_props(param_src: str) -> list[dict]:
    param_src = param_src.strip()
    m = re.search(r"\{(.*)\}", param_src, re.DOTALL)
    if not m:
        return []
    inner = m.group(1)
    props = []
    depth, buf = 0, ""
    # split on top-level commas (defaults may contain commas inside {}/[]/())
    for ch in inner:
        if ch in "{[(":
            depth += 1
        elif ch in "}])":
            depth -= 1
        if ch == "," and depth == 0:
            props.append(buf); buf = ""
        else:
            buf += ch
    if buf.strip():
        props.append(buf)
    out = []
    for raw in props:
        raw = raw.strip()
        if not raw or raw.startswith("..."):
            continue
        if "=" in raw:
            name, default = raw.split("=", 1)
            name, default = name.strip(), default.strip()
        else:
            name, default = raw, None
        if not re.match(r"^[A-Za-z_$][\w$]*$", name):
            continue
        out.append({"name": name, "default": default, "type": infer_type(default)})
    return out


def infer_type(default: str | None) -> str:
    if default is None:
        return "unknown"
    d = default.strip()
    if d in ("true", "false"):
        return "boolean"
    if re.match(r"^-?\d+(\.\d+)?$", d):
        return "number"
    if (d.startswith("'") or d.startswith('"') or d.startswith("`")):
        return "string"
    if d.startswith("[") or d.startswith("{"):
        return "object"
    if d in ("undefined", "null"):
        return "unknown"
    return "expression"


# Screens (page-level components) vs reusable library components.
SCREEN_RE = re.compile(r"(Page|Screen|Splash|View|Route)$")
SCREEN_ONLY_PROPS = {"navigate", "route", "router", "setRoute", "goTo"}
# Reusable-control name heuristic — page-local components worth promoting to the lib.
CONTROL_RE = re.compile(
    r"^(Input|Textarea|Toggle|Switch|Checkbox|Radio|Select|Field|Form|Tab|Tabs|"
    r"Seg|Segmented|Slider|Dropdown|Menu|Tooltip|KPI|Stat|StatCell|MiniCard|"
    r"SmallStat|RepoStat|Pill|FilterPill|Chip|MiniTab)([A-Z].*)?$"
)
# Did the SOURCE itself use React Aria? (claude.ai exports almost never do.)
RAC_RE = re.compile(r"react-aria|@react-aria|useButton|useToggle|AriaButton|AriaLink|"
                    r"react-aria-components")


def extract_window_members(text: str) -> set[str]:
    """Names inside Object.assign(window, {A, B, C}) blocks — the strongest
    public-API signal in a claude.ai export (the prototype's own export list)."""
    members: set[str] = set()
    for blk in WINDOW_EXPORT.findall(text):
        members.update(re.findall(r"[A-Z][A-Za-z0-9_]*", blk))
    return members


def is_screen(name: str, props: list[dict]) -> bool:
    if SCREEN_RE.search(name) or name == "App":
        return True
    pnames = {p["name"] for p in props}
    # A component whose only inputs are navigation handles is a screen, not a primitive.
    return bool(pnames) and pnames.issubset(SCREEN_ONLY_PROPS)


def extract_components(text: str) -> list[dict]:
    comps: dict[str, dict] = {}
    for m in COMP_DEF.finditer(text):
        name = m.group(1) or m.group(3)
        params = m.group(2) if m.group(1) else m.group(4)
        if not name or name in ("App",) and False:
            pass
        if not name:
            continue
        # skip obvious hooks/helpers wrongly matched (PascalCase guard already helps)
        props = parse_props(params or "")
        # keep the first/most-detailed definition seen
        prev = comps.get(name)
        if prev is None or len(props) > len(prev["props"]):
            comps[name] = {"name": name, "props": props}
    # which ones are explicitly exported?
    exported: set[str] = set()
    for blk in WINDOW_EXPORT.findall(text):
        exported.update(re.findall(r"[A-Z][A-Za-z0-9_]*", blk))
    for blk in NAMED_EXPORT.findall(text):
        exported.update(re.findall(r"[A-Z][A-Za-z0-9_]*", blk))
    for mm in re.finditer(r"export\s+(?:default\s+)?(?:function|const)\s+([A-Z][A-Za-z0-9_]*)", text):
        exported.add(mm.group(1))
    result = []
    for name, c in comps.items():
        c["exported"] = name in exported
        result.append(c)
    return result


def detect_framework(files: list[dict]) -> str:
    exts = [f["ext"] for f in files]
    text_all = ""  # cheap signal from extensions
    if ".svelte" in exts:
        return "svelte"
    if ".vue" in exts:
        return "vue"
    has_tsx = ".tsx" in exts
    has_jsx = ".jsx" in exts
    if has_tsx:
        return "react-tsx"
    if has_jsx:
        return "react-jsx"
    if any(e in exts for e in (".js", ".ts")):
        return "react-or-vanilla-js"
    if ".html" in exts:
        return "html"
    return "unknown"


# -----------------------------------------------------------------------------
# Driver
# -----------------------------------------------------------------------------

SKIP_DIRS = {"__MACOSX", "node_modules", ".git"}


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Analyze a Claude design-export zip.")
    ap.add_argument("target", help="Path to .zip or an already-extracted directory")
    ap.add_argument("--out", default=None, help="Where to write analysis.json")
    ap.add_argument("--extract-to", default=None, help="Dir to extract the zip into")
    args = ap.parse_args()

    target = Path(args.target).expanduser()
    if not target.exists():
        print(f"ERROR: {target} does not exist", file=sys.stderr)
        return 2

    # Resolve a root directory of extracted files.
    if target.is_dir():
        root = target
    else:
        dest = Path(args.extract_to).expanduser() if args.extract_to \
            else Path(tempfile.mkdtemp(prefix="design_zip_"))
        dest.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(target) as zf:
            zf.extractall(dest)
        root = dest
        # If the zip wrapped everything in a single top folder, descend into it.
        kids = [p for p in root.iterdir() if p.name not in SKIP_DIRS]
        if len(kids) == 1 and kids[0].is_dir():
            root = kids[0]

    files: list[dict] = []
    tokens_files: list[dict] = []
    components_by_file: dict[str, list[dict]] = {}
    window_members: set[str] = set()
    react_aria_hit = False

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            full = Path(dirpath) / fn
            rel = str(full.relative_to(root))
            ext = full.suffix.lower()
            size = full.stat().st_size
            text = read_text(full) if (ext in CODE_EXTS or ext in STYLE_EXTS
                                       or ext == ".json" or ext == ".html") else None
            role = classify(rel, ext, text)
            entry = {"path": rel, "ext": ext, "size": size, "role": role}
            files.append(entry)

            if role == "tokens" and ext in STYLE_EXTS and text:
                tk = extract_css_tokens(text)
                tk["path"] = rel
                tokens_files.append(tk)
            if role in ("primitives", "composite", "page", "code", "entry") and \
               ext in {".jsx", ".tsx", ".js", ".ts"} and text:
                comps = extract_components(text)
                if comps:
                    components_by_file[rel] = comps
                window_members |= extract_window_members(text)
                if RAC_RE.search(text):
                    react_aria_hit = True

    framework = detect_framework(files)

    # Roll up roles
    by_role: dict[str, list[str]] = {}
    for f in files:
        by_role.setdefault(f["role"], []).append(f["path"])

    # Flatten component inventory (dedupe by name, prefer exported + most props)
    flat: dict[str, dict] = {}
    for rel, comps in components_by_file.items():
        for c in comps:
            c = {**c, "file": rel}
            prev = flat.get(c["name"])
            score = (1 if c.get("exported") else 0, len(c["props"]))
            pscore = (1 if prev and prev.get("exported") else 0,
                      len(prev["props"]) if prev else -1)
            if prev is None or score > pscore:
                flat[c["name"]] = c
    components = sorted(flat.values(), key=lambda c: (not c.get("exported"), c["name"]))

    # ---- Annotate components: public-API tier + screen vs primitive ----
    # `exported` over-reports (a claude.ai export writes pages as `export function
    # FooPage()`), so we add a stronger `public` signal (membership in the
    # Object.assign(window, {…}) list) and split screens out from library primitives.
    path_role = {f["path"]: f["role"] for f in files}
    for c in components:
        c["window_member"] = c["name"] in window_members
        c["public"] = bool(c["window_member"] or c.get("exported"))
        c["screen"] = is_screen(c["name"], c["props"])
        role = path_role.get(c.get("file"), "")
        # A layout component living in a composite file (Sidebar/TopBar) can take
        # `route`/`navigate` props without being a screen — only its NAME decides.
        if role == "composite" and not SCREEN_RE.search(c["name"]):
            c["screen"] = False
        if c["screen"]:
            c["kind"] = "screen"
        elif role == "composite":
            c["kind"] = "composite"
        elif c["public"]:
            c["kind"] = "primitive"
        else:
            c["kind"] = "local"

    # The curated set to confirm in Phase 2 (not re-derive): public, non-screen
    # components + layout composites.
    recommended = [c["name"] for c in components
                   if not c["screen"] and (c["public"] or c["kind"] == "composite")]
    # Page-local components that LOOK reusable (form/metric controls) — promote-on-confirm.
    promotion_candidates = [c["name"] for c in components
                            if c["kind"] == "local" and not c["screen"]
                            and CONTROL_RE.match(c["name"])]
    screens = [c["name"] for c in components if c["screen"] and c["name"] != "App"]

    # Merge token scopes across all token sheets
    merged_scopes: dict[str, dict] = {}
    themes: set[str] = set()
    fonts: list[str] = []
    for tk in tokens_files:
        for sel, vars_ in tk["scopes"].items():
            merged_scopes.setdefault(sel, {}).update(vars_)
        themes.update(tk["themes"])
        for fu in tk["fonts"]:
            if fu not in fonts:
                fonts.append(fu)
    token_total = sum(len(v) for v in merged_scopes.values())

    analysis = {
        "root": str(root),
        "source_framework": framework,
        "counts": {role: len(paths) for role, paths in sorted(by_role.items())},
        "files_by_role": by_role,
        "tokens": {
            "files": [t["path"] for t in tokens_files],
            "themes": sorted(themes),
            "fonts": fonts,
            "total_variables": token_total,
            "scopes": merged_scopes,
        },
        "components": components,
        "component_count": len(components),
        # The curated lists the generator should ACT on (confirm in Phase 2):
        "recommended_library_components": recommended,
        "promotion_candidates": promotion_candidates,
        "screens": screens,
        "source_uses_react_aria": react_aria_hit,
        "pages": by_role.get("page", []),
        "composites": by_role.get("composite", []),
        "assets": by_role.get("asset", []),
        "screenshots": by_role.get("screenshot", []),
        "html_entries": by_role.get("html", []),
    }

    out_path = Path(args.out).expanduser() if args.out else (root / "analysis.json")
    out_path.write_text(json.dumps(analysis, indent=2), encoding="utf-8")

    # ---- Human-readable summary to stdout ----
    print("=" * 64)
    print("DESIGN ZIP ANALYSIS")
    print("=" * 64)
    print(f"root:              {root}")
    print(f"source framework:  {framework}")
    print(f"themes detected:   {', '.join(sorted(themes)) or '(none / single)'}")
    print(f"token variables:   {token_total} across {len(merged_scopes)} scope(s)")
    print(f"token sheets:      {', '.join(analysis['tokens']['files']) or '(none)'}")
    print(f"components found:   {len(components)} "
          f"(recommend {len(recommended)} for the library)")
    print(f"source React Aria: {'yes' if react_aria_hit else 'no'}")
    print(f"pages / screens:   {len(analysis['pages'])} files / {len(screens)} screen components")
    print(f"composites:        {len(analysis['composites'])}")
    print("-" * 64)
    print("Roles:")
    for role, paths in sorted(by_role.items()):
        print(f"  {role:12} {len(paths):3}  {', '.join(paths[:4])}"
              + (" ..." if len(paths) > 4 else ""))
    print("-" * 64)
    print(f"RECOMMENDED library components ({len(recommended)}): {', '.join(recommended)}")
    if promotion_candidates:
        print(f"PROMOTION candidates (page-local but reusable): {', '.join(promotion_candidates)}")
    if screens:
        print(f"SCREENS (rebuild as pages, not library): {', '.join(screens)}")
    print("-" * 64)
    print("Full component inventory (name — kind — #props — public):")
    for c in components:
        pub = "pub" if c.get("public") else "   "
        print(f"  [{pub}] {c['kind']:10} {c['name']:20} props={len(c['props']):2}  "
              f"({', '.join(p['name'] for p in c['props'][:5])}"
              + (" ..." if len(c['props']) > 5 else "") + ")")
    print("-" * 64)
    print(f"analysis.json -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
