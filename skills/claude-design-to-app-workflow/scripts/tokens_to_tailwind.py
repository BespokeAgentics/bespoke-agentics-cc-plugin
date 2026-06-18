#!/usr/bin/env python3
"""
tokens_to_tailwind.py — Turn a design export's CSS custom properties into a
Tailwind v4 `@theme inline` layer, WITHOUT losing runtime dark/light theming.

Why `@theme inline`:
  Tailwind v4 generates utilities from `@theme` tokens. If you map a semantic
  token to a *value* (e.g. --color-accent: #60a5fa) the utility bakes the value
  in and a runtime `[data-theme="light"]` swap won't move it. With
  `@theme inline { --color-accent: var(--accent-default); }` the generated
  `bg-accent` utility resolves to `var(--accent-default)` AT USE SITE, so when
  the source's own `[data-theme]` blocks reassign `--accent-default`, every
  `bg-accent` updates live. That is exactly the behavior these claude.ai design
  exports rely on (dark default + `[data-theme="light"]` override).

So the strategy is:
  1. KEEP the source token sheet (tokens.css) verbatim — it is the runtime
     variable + theme-switch layer. Import it first.
  2. EMIT `tailwind-theme.css`: `@import "tailwindcss";` then an `@theme inline`
     block that re-exposes the source vars under Tailwind's namespaces
     (--color-*, --font-*, --text-*, --radius-*, --spacing-*, --shadow-*,
      --leading-*, --tracking-*, --font-weight-*), referencing the source vars.
  3. EMIT `tokens.index.json`: structured token data + a `css_var_usage` map the
     component converter uses to rewrite inline styles into utility classes,
     e.g.  background: 'var(--accent-default)'  ->  className="bg-accent".

The emitted theme is a strong DRAFT. Token names differ per export, so review
the role-color naming (fg/surface/border/accent) — see references/tokens-and-tailwind.md.

Usage:
    python3 tokens_to_tailwind.py <tokens.css> [--out-dir DIR] [--analysis analysis.json]
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

CSS_VAR_DECL = re.compile(r"--([A-Za-z0-9][\w-]*)\s*:\s*([^;{}]+);")
SELECTOR_BLOCK = re.compile(r"([^{}]+)\{([^{}]*)\}", re.DOTALL)
THEME_SELECTOR = re.compile(r'\[data-theme\s*=\s*["\']?([\w-]+)["\']?\]')

HEXLIKE = re.compile(r"#[0-9a-fA-F]{3,8}\b")
COLORFUNC = re.compile(r"\b(rgb|rgba|hsl|hsla|oklch|oklab|color)\s*\(")


# -----------------------------------------------------------------------------
# Categorize a token by its name + value into a Tailwind v4 namespace.
# -----------------------------------------------------------------------------

def is_color_value(val: str) -> bool:
    return bool(HEXLIKE.search(val) or COLORFUNC.search(val))


def categorize(name: str, value: str, var_lookup: dict[str, str]) -> str | None:
    """Return Tailwind theme namespace key (without trailing token name), or None."""
    n = name.lower()
    v = value.strip()

    # Resolve one level of var() to judge color-ness (e.g. --accent: var(--blue-400))
    resolved = v
    m = re.match(r"var\(\s*--([\w-]+)\s*\)", v)
    if m and m.group(1) in var_lookup:
        resolved = var_lookup[m.group(1)]

    # Fonts ----------------------------------------------------------------
    if "font-family" in n or (("font" in n) and ("," in v or "serif" in v or "sans" in v or "mono" in v)):
        return "font"
    if re.search(r"\b(fw|weight)\b", n) and re.match(r"^\d{2,3}$", v):
        return "font-weight"
    # Type sizes -----------------------------------------------------------
    if re.search(r"\b(fs|font-size|text)\b", n) and re.search(r"(rem|em|px)\b", v):
        return "text"
    # Line height / tracking ----------------------------------------------
    if re.search(r"\b(lh|line-height|leading)\b", n):
        return "leading"
    if re.search(r"\b(ls|letter|tracking)\b", n):
        return "tracking"
    # Radius ---------------------------------------------------------------
    if "radius" in n or n.endswith("-r") or "rounded" in n:
        return "radius"
    # Shadow ---------------------------------------------------------------
    if "shadow" in n or "elevation" in n:
        return "shadow"
    # Spacing --------------------------------------------------------------
    if re.search(r"\b(sp|space|spacing|gap|gutter|size)\b", n) and re.search(r"(px|rem|em)\b", v):
        return "spacing"
    # Colors (by value) — do this last so named scales fall through to here.
    if is_color_value(resolved):
        return "color"
    return None


def clean_token_name(name: str) -> str:
    """Strip common prefixes so --accent-default -> accent-default, --fs-body-m -> body-m."""
    for pre in ("color-", "clr-", "fs-", "fw-", "lh-", "ls-", "sp-", "space-",
                "radius-", "shadow-", "font-"):
        if name.startswith(pre):
            return name[len(pre):]
    return name


# Map a source color var name to a friendlier role name to avoid awkward
# utilities like `text-text-primary`. Heuristic + safe fallback.
ROLE_RENAMES = [
    (re.compile(r"^text-primary$"), "fg"),
    (re.compile(r"^text-heading$"), "fg-heading"),
    (re.compile(r"^text-secondary$"), "fg-muted"),
    (re.compile(r"^text-muted$"), "fg-subtle"),
    (re.compile(r"^text-(.+)$"), r"fg-\1"),
    (re.compile(r"^surface-default$"), "surface"),
    (re.compile(r"^surface-(.+)$"), r"surface-\1"),
    (re.compile(r"^border-default$"), "border"),
    (re.compile(r"^border-(.+)$"), r"border-\1"),
    (re.compile(r"^accent-default$"), "accent"),
    (re.compile(r"^accent-(.+)$"), r"accent-\1"),
]


def role_color_name(token: str) -> str:
    for pat, repl in ROLE_RENAMES:
        if pat.match(token):
            return pat.sub(repl, token)
    return token


NS_PREFIX = {
    "color": "color",
    "font": "font",
    "font-weight": "font-weight",
    "text": "text",
    "leading": "leading",
    "tracking": "tracking",
    "radius": "radius",
    "shadow": "shadow",
    "spacing": "spacing",
}

# For the inline-style -> utility map: CSS property -> Tailwind utility prefix
# for color tokens, plus a few size mappings.
COLOR_PROP_UTILITY = {
    "color": "text-",
    "background": "bg-",
    "background-color": "bg-",
    "border-color": "border-",
    "fill": "fill-",
    "stroke": "stroke-",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("tokens_css", help="Path to the source token stylesheet")
    ap.add_argument("--out-dir", default=".")
    ap.add_argument("--analysis", default=None, help="optional analysis.json (unused but reserved)")
    args = ap.parse_args()

    src = Path(args.tokens_css).expanduser()
    if not src.exists():
        print(f"ERROR: {src} not found", file=sys.stderr)
        return 2
    out_dir = Path(args.out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    text = src.read_text(encoding="utf-8", errors="replace")

    # Gather scopes.
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

    # Global (theme-independent) vars = anything declared in a :root-only scope
    # that is NOT also overridden per theme. We treat the union of all vars as
    # the lookup, but only emit ONE @theme mapping per token name.
    var_lookup: dict[str, str] = {}
    for sel, vars_ in scopes.items():
        for k, v in vars_.items():
            var_lookup.setdefault(k, v)

    # Which vars are theme-dependent (declared under a [data-theme] selector)?
    theme_vars: set[str] = set()
    for sel, vars_ in scopes.items():
        if "data-theme" in sel:
            theme_vars.update(vars_.keys())

    # Build the @theme inline mapping. Each entry: tw_token -> source var ref.
    # tw_token already includes namespace prefix, e.g. color-accent, radius-md.
    theme_entries: dict[str, str] = {}      # "--color-accent" -> "var(--accent-default)"
    css_var_to_color_token: dict[str, str] = {}  # "accent-default" -> "accent"  (role name)
    categorized: dict[str, list] = {}

    for name in sorted(var_lookup.keys()):
        value = var_lookup[name]
        cat = categorize(name, value, var_lookup)
        if cat is None:
            continue
        base = clean_token_name(name)
        if cat == "color":
            base = role_color_name(base)
            css_var_to_color_token[name] = base
        ns = NS_PREFIX[cat]
        tw_token = f"{ns}-{base}"
        # Avoid duplicate keys (e.g. two vars cleaning to same name) — first wins.
        if tw_token in theme_entries:
            tw_token = f"{ns}-{name}"  # fall back to the raw var name
        theme_entries[tw_token] = f"var(--{name})"
        categorized.setdefault(cat, []).append({"var": name, "token": tw_token, "value": value})

    # ---- Write tailwind-theme.css ----
    lines = [
        '@import "tailwindcss";',
        "",
        "/* The source token sheet (runtime vars + [data-theme] switching) must be",
        "   imported BEFORE this file so the var() references below resolve and so",
        "   theme switching keeps working. e.g. in your entry CSS:",
        '     @import "./tokens.css";   (* the verbatim source sheet *)',
        '     @import "./tailwind-theme.css";',
        "*/",
        "",
    ]
    if themes:
        # Rewire Tailwind's dark: variant to follow the source's [data-theme] attr
        # instead of OS preference, so `dark:` utilities track the app toggle.
        if "dark" in themes:
            lines += [
                '/* Make the `dark:` variant follow [data-theme="dark"] (the source\'s'
                ' toggle), not the OS setting. */',
                '@custom-variant dark (&:where([data-theme="dark"], [data-theme="dark"] *));',
                "",
            ]
    lines.append("@theme inline {")
    # group output by namespace for readability
    order = ["color", "font", "font-weight", "text", "leading", "tracking",
             "radius", "spacing", "shadow"]
    by_ns: dict[str, list[tuple[str, str]]] = {}
    for tok, ref in theme_entries.items():
        ns = tok.split("-", 1)[0] if not tok.startswith("font-weight") else "font-weight"
        # normalize ns key
        for cand in order:
            if tok.startswith(cand + "-"):
                ns = cand
                break
        by_ns.setdefault(ns, []).append((tok, ref))
    for ns in order:
        items = by_ns.get(ns)
        if not items:
            continue
        lines.append(f"  /* {ns} */")
        for tok, ref in sorted(items):
            lines.append(f"  --{tok}: {ref};")
        lines.append("")
    lines.append("}")
    theme_css = "\n".join(lines) + "\n"
    (out_dir / "tailwind-theme.css").write_text(theme_css, encoding="utf-8")

    # ---- Write tokens.index.json ----
    # css_var_usage helps the converter: for each color var, what utility to emit
    # depending on the CSS property it was used in.
    css_var_usage = {}
    for var_name, color_token in css_var_to_color_token.items():
        css_var_usage[var_name] = {
            prop: f"{util}{color_token}" for prop, util in COLOR_PROP_UTILITY.items()
        }
    index = {
        "source": str(src),
        "themes": themes,
        "theme_dependent_vars": sorted(theme_vars),
        "namespaces": {k: categorized.get(k, []) for k in order},
        "theme_inline_map": theme_entries,
        "color_var_to_token": css_var_to_color_token,
        "css_var_usage": css_var_usage,
    }
    (out_dir / "tokens.index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")

    # ---- Summary ----
    print("=" * 60)
    print("TOKENS -> TAILWIND v4")
    print("=" * 60)
    print(f"source:        {src}")
    print(f"themes:        {', '.join(themes) or '(single)'}")
    print(f"theme tokens emitted: {len(theme_entries)}")
    for ns in order:
        items = by_ns.get(ns)
        if items:
            print(f"  {ns:12} {len(items):3}")
    print("-" * 60)
    print(f"wrote: {out_dir/'tailwind-theme.css'}")
    print(f"wrote: {out_dir/'tokens.index.json'}")
    print()
    print("NOTE: role-color names (fg/surface/border/accent) are a heuristic draft.")
    print("Review references/tokens-and-tailwind.md before finalizing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
