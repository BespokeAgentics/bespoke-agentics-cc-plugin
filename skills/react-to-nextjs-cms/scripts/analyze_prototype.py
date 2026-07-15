#!/usr/bin/env python3
"""
analyze_prototype.py — Inventory a runtime-Babel React prototype (a claude.ai "omelette"
style site) so the agent skips the rote reading. Writes analysis.json in the shape
documented in references/analysis.md.

It detects the in-browser-Babel runtime, the HTML entries, the site/*.jsx pages, the _ds
design-system bundle (tokens, manifest, components, window namespace), image-slot usage,
the tweaks/EDITMODE block, fonts, and — most importantly — content_candidates: the
hardcoded strings/images in the JSX that should become editable Tina fields.

Dependency-free (stdlib only). Heuristic by design: it is generous with
content_candidates; the agent confirms which are real content in Phase 2.

Usage:
    python3 analyze_prototype.py <source-dir> --out analysis.json
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

SNAPSHOT_MIN_BYTES = 300_000  # a huge single-file .html is a rendered snapshot, not source


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def rel(p: Path, root: Path) -> str:
    try:
        return str(p.relative_to(root))
    except ValueError:
        return str(p)


def detect_runtime(html_texts: list[str]) -> str:
    blob = "\n".join(html_texts)
    if "@babel/standalone" in blob and re.search(r"react(-dom)?[@/.]", blob):
        return "react-babel-standalone"
    if "@babel/standalone" in blob:
        return "babel-standalone"
    return "unknown"


def find_fonts(texts: list[str]) -> list[str]:
    fonts: list[str] = []
    for t in texts:
        for m in re.findall(r"https://fonts\.googleapis\.com/css2\?[^\"')]+", t):
            if m not in fonts:
                fonts.append(m)
    return fonts


def parse_editmode(html_texts: list[str]) -> dict:
    for t in html_texts:
        m = re.search(r"/\*EDITMODE-BEGIN\*/(.*?)/\*EDITMODE-END\*/", t, re.DOTALL)
        if m:
            raw = m.group(1).strip()
            try:
                return json.loads(raw)
            except Exception:
                # tolerate trailing commas / single quotes
                cleaned = re.sub(r",(\s*[}\]])", r"\1", raw).replace("'", '"')
                try:
                    return json.loads(cleaned)
                except Exception:
                    return {}
    return {}


def parse_tweak_controls(html_texts: list[str]) -> list[dict]:
    controls: list[dict] = []
    seen = set()
    blob = "\n".join(html_texts)
    # setTweak('key', …) calls name the keys the panel writes.
    for key in re.findall(r"setTweak\(\s*['\"](\w+)['\"]", blob):
        if key not in seen:
            seen.add(key)
            controls.append({"key": key})
    kinds = sorted(set(re.findall(r"Tweak(Radio|Select|Toggle|Slider|Color|Text|Number)\b", blob)))
    return [{"key": c["key"]} for c in controls] + ([{"control_kinds": kinds}] if kinds else [])


CONTENT_PROP = re.compile(
    r"\b(headline|title|subhead|sub|eyebrow|label|body|text|cta|heading|name|quote|author|"
    r"description|caption|blurb|tagline|phone|email|address|hours)\s*[:=]\s*['\"]([^'\"]{2,200})['\"]"
)
JSX_TEXT = re.compile(r">\s*([^<>{}][^<>{}]*?)\s*<")
NOISE = re.compile(r"(=>|className|import |const |function |return |http[s]?://|^\d+$|^[a-z-]+$)")


def looks_like_content(s: str) -> bool:
    s = s.strip()
    if len(s) < 3 or len(s) > 240:
        return False
    if not re.search(r"[A-Za-z]", s):
        return False
    if NOISE.search(s):
        # allow ALL-CAPS eyebrows even though they'd match ^[a-z-]+$? no, uppercase passes
        if not (s.isupper() and " " in s):
            return False
    words = s.split()
    return len(words) >= 2 or s.endswith((".", "!", "?", ":")) or s.isupper()


def extract_candidates(jsx_path: Path, root: Path, page_id: str, cap: int = 60) -> list[dict]:
    text = read(jsx_path)
    out: list[dict] = []
    seen = set()

    def add(kind: str, value: str, extra: dict | None = None):
        key = (kind, value)
        if value in seen or key in seen:
            return
        seen.add(value)
        rec = {"page": page_id, "kind": kind, "text": value}
        if extra:
            rec.update(extra)
        out.append(rec)

    for m in CONTENT_PROP.finditer(text):
        add("prop:" + m.group(1), m.group(2))
    for m in JSX_TEXT.finditer(text):
        s = m.group(1).strip()
        if looks_like_content(s):
            add("jsx-text", s)
    # image slots on this page
    slots = len(re.findall(r"<image-slot", text)) + len(re.findall(r"ImageSlot", text))
    if slots:
        out.append({"page": page_id, "kind": "image", "count": slots})
    return out[:cap]


def analyze_design_system(root: Path) -> dict:
    ds_dirs = [p for p in root.glob("_ds/*") if p.is_dir()]
    if not ds_dirs:
        # sometimes nested one level up
        ds_dirs = [p for p in root.glob("**/_ds/*") if p.is_dir()][:1]
    if not ds_dirs:
        return {}
    ds = ds_dirs[0]
    manifest_path = next(iter(ds.glob("_ds_manifest.json")), None)
    bundle_path = next(iter(ds.glob("_ds_bundle.js")), None)
    tokens = [rel(p, root) for p in sorted(ds.glob("tokens/*.css"))]
    styles = next(iter(ds.glob("styles.css")), None)

    components: list[dict] = []
    namespace = None
    if manifest_path:
        try:
            man = json.loads(read(manifest_path))
            # manifests vary; pull component names generously
            if isinstance(man, dict):
                namespace = man.get("namespace") or man.get("window") or man.get("id")
                comp_src = man.get("components") or man.get("exports") or []
                if isinstance(comp_src, dict):
                    comp_src = list(comp_src.values())
                for c in comp_src:
                    if isinstance(c, str):
                        components.append({"name": c})
                    elif isinstance(c, dict) and c.get("name"):
                        components.append({"name": c["name"], "props": c.get("props", [])})
        except Exception:
            pass
    if not namespace and bundle_path:
        m = re.search(r"window\.(ProTec\w+|[A-Z]\w+DesignSystem\w*)", read(bundle_path))
        if m:
            namespace = m.group(1)

    return {
        "id": ds.name,
        "dir": rel(ds, root),
        "bundle": rel(bundle_path, root) if bundle_path else None,
        "manifest": rel(manifest_path, root) if manifest_path else None,
        "window_namespace": namespace,
        "tokens": tokens,
        "styles_entry": rel(styles, root) if styles else None,
        "components": components,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Inventory a runtime-Babel React prototype.")
    ap.add_argument("source", help="Prototype source directory (has index.html + site/*.jsx + _ds/)")
    ap.add_argument("--out", default="analysis.json", help="Where to write the manifest")
    args = ap.parse_args()

    root = Path(args.source).expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"ERROR: not a directory: {root}")

    html_files = sorted(root.glob("*.html")) + sorted(root.glob("**/*.html"))
    html_files = list(dict.fromkeys(html_files))
    html_entries, snapshots, html_texts = [], [], []
    for h in html_files:
        size = h.stat().st_size if h.exists() else 0
        if size >= SNAPSHOT_MIN_BYTES:
            snapshots.append({"file": rel(h, root), "bytes": size})
        else:
            html_entries.append(rel(h, root))
            html_texts.append(read(h))

    # pages: site/*.jsx (and top-level *.jsx that aren't the tweaks panel)
    jsx_files = sorted(root.glob("site/*.jsx")) + sorted(root.glob("*.jsx"))
    jsx_files = list(dict.fromkeys(jsx_files))
    pages, shared_components, candidates = [], [], []
    blob = "\n".join(html_texts)
    for j in jsx_files:
        name = j.stem
        low = name.lower()
        if "tweaks-panel" in low:
            continue
        if low in ("shared", "chrome", "layout", "nav"):
            shared_components.append(rel(j, root))
            candidates += extract_candidates(j, root, low)
            continue
        # find the window export this page mounts, e.g. window.ProTecHome
        win = None
        mexp = re.search(r"window\.(ProTec\w+|[A-Z]\w+)\s*=", read(j))
        if mexp:
            win = mexp.group(1)
        mounted = None
        for he in html_entries:
            if re.search(rf'src=["\']site/{re.escape(j.name)}', blob) or (win and win in blob):
                mounted = he
                break
        props_from_tweaks = sorted(set(re.findall(r"\bt\.(\w+)", read(j))))[:12]
        pages.append({
            "id": low,
            "jsx": rel(j, root),
            "window_export": win,
            "mounted_by": mounted,
            "props_from_tweaks": props_from_tweaks,
        })
        candidates += extract_candidates(j, root, low)

    manifest = {
        "runtime": detect_runtime(html_texts),
        "source_dir": str(root),
        "html_entries": html_entries,
        "rendered_snapshots": snapshots,
        "pages": pages,
        "shared_components": shared_components,
        "design_system": analyze_design_system(root),
        "image_slots": {
            "custom_element": "image-slot.js" if (root / "image-slot.js").exists()
            else (rel(next(iter(root.glob("**/image-slot.js")), Path()), root) or None),
            "uses": sum(c.get("count", 0) for c in candidates if c.get("kind") == "image"),
        },
        "tweaks": {
            "panel": rel(next(iter(root.glob("**/tweaks-panel.jsx")), Path()), root)
            if list(root.glob("**/tweaks-panel.jsx")) else None,
            "defaults": parse_editmode(html_texts),
            "controls": parse_tweak_controls(html_texts),
        },
        "fonts": find_fonts(html_texts + [read(p) for p in root.glob("**/*.css")][:20]),
        "content_candidates": candidates,
        "counts": {
            "html_entries": len(html_entries),
            "pages": len(pages),
            "content_candidates": len(candidates),
        },
    }

    out = Path(args.out).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    ds = manifest["design_system"]
    print(f"Analyzed {root}")
    print(f"  runtime: {manifest['runtime']}")
    print(f"  pages: {len(pages)}  ({', '.join(p['id'] for p in pages) or '—'})")
    print(f"  design system: {ds.get('id', '—')}  components={len(ds.get('components', []))}  tokens={len(ds.get('tokens', []))}")
    print(f"  content candidates: {len(candidates)}  (confirm which are real content in Phase 2)")
    print(f"  tweaks defaults: {list(manifest['tweaks']['defaults'].keys()) or '—'}")
    print(f"  wrote: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
