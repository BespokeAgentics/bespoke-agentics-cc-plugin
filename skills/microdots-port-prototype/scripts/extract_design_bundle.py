#!/usr/bin/env python3
"""Extract the original source tree from a Claude Design bundler artifact.

A Claude Design "standalone HTML" export is not minified output: it carries the
hand-written source in `<script type="__bundler/manifest">` as gzip+base64 blobs
keyed by UUID, plus the real page shell in `<script type="__bundler/template">`.
This script recovers all of it deterministically -- module load order, roles,
and names -- so downstream analysis reads real source with real file:line
anchors instead of guessing from pixels.

Usage:
    extract_design_bundle.py <artifact.html|dir|zip> --out <dir> [--quiet]
    extract_design_bundle.py <artifact> --check        # detect only, no writes

Exit codes:
    0  extracted (or --check passed)
    2  not a Claude Design bundler artifact
    3  artifact found but malformed (manifest/template unreadable)
"""

from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import os
import re
import sys
import tempfile
import zipfile

MANIFEST_RE = re.compile(
    r'<script type="__bundler/manifest">\s*(\{.*?\})\s*</script>', re.S
)
TEMPLATE_RE = re.compile(
    r'<script type="__bundler/template">\s*("(?:[^"\\]|\\.)*")\s*</script>', re.S
)
SECTION_RE = re.compile(
    r'<script type="__bundler/(ext_resources|page_order)">\s*(.*?)\s*</script>', re.S
)
SCRIPT_TAG_RE = re.compile(r'<script\b([^>]*)>(.*?)</script>', re.S | re.I)
ATTR_RE = re.compile(r'([\w:-]+)\s*=\s*"([^"]*)"')
STYLE_RE = re.compile(r'<style\b[^>]*>(.*?)</style>', re.S | re.I)

# First-line name hints Claude Design modules carry, e.g. "// tweaks-panel.jsx".
NAME_COMMENT_RE = re.compile(
    r'^\s*(?://|/\*|\*)\s*([\w.-]+\.(?:jsx?|tsx?|mjs|css))\s*$', re.M
)
# Fallback: a banner title line, e.g. "//  Foundry Context Engine - mock data store".
BANNER_RE = re.compile(r'^\s*//\s{1,4}([A-Z][^\n]{3,60}?)\s*$', re.M)

# Claude Design ships two export shapes. Both declare app source in the template,
# but differently:
#   babel-modules -- many <script type="text/babel" src="<uuid>"> app modules.
#   dc-runtime    -- one inline <script type="text/x-dc" data-dc-script> component,
#                    with only the dc-runtime bundle and React in the manifest.
# A plain <script src> is a vendor library in both shapes.
APP_SCRIPT_TYPES = {"text/babel", "text/jsx", "text/x-dc"}

EXT_BY_MIME = {
    "text/jsx": ".jsx",
    "text/javascript": ".js",
    "application/javascript": ".js",
    "text/css": ".css",
    "application/json": ".json",
    "image/svg+xml": ".svg",
}

def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:48] or "module"


def find_artifact(target: str, tmpdir: str) -> str:
    """Resolve an HTML file, a directory, or a zip to a single artifact path."""
    if os.path.isfile(target) and target.lower().endswith(".zip"):
        with zipfile.ZipFile(target) as zf:
            zf.extractall(tmpdir)
        target = tmpdir
    if os.path.isfile(target):
        return target
    if os.path.isdir(target):
        hits = []
        for root, _dirs, files in os.walk(target):
            for name in files:
                if name.lower().endswith((".html", ".htm")):
                    path = os.path.join(root, name)
                    try:
                        with open(path, encoding="utf-8", errors="replace") as fh:
                            if '__bundler/manifest' in fh.read(400_000):
                                hits.append(path)
                    except OSError:
                        continue
        if len(hits) == 1:
            return hits[0]
        if not hits:
            die(2, f"no Claude Design artifact found under {target}")
        die(2, "multiple Claude Design artifacts found; pass one explicitly:\n  "
               + "\n  ".join(sorted(hits)))
    die(2, f"not a file or directory: {target}")
    raise AssertionError  # unreachable


def die(code: int, message: str) -> None:
    sys.stderr.write(f"error: {message}\n")
    if code == 2:
        sys.stderr.write(
            "hint: this skill only accepts Claude Design exports (an HTML file "
            'carrying <script type="__bundler/manifest">). For a real app '
            "directory use microdots-port-app; for a Storybook use funcspec.\n"
        )
    sys.exit(code)


def decode_asset(entry: dict) -> bytes:
    raw = base64.b64decode(entry["data"])
    if entry.get("compressed"):
        raw = gzip.decompress(raw)
    return raw


def guess_name(text: str, fallback: str) -> tuple[str, str | None, str | None]:
    """Return (basename, declared_name, banner).

    A filename is only ever taken from an actual filename comment. A banner
    comment is a useful hint but is NOT a name -- it is carried as metadata so
    the filename never claims more than the source stated.
    """
    head = text[:2000]
    banner_match = BANNER_RE.search(head)
    banner = banner_match.group(1).strip() if banner_match else None
    match = NAME_COMMENT_RE.search(head)
    if match:
        return match.group(1), match.group(1), banner
    return fallback, None, banner


def main() -> None:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("artifact")
    parser.add_argument("--out", default=None)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmpdir:
        path = find_artifact(args.artifact, tmpdir)
        with open(path, encoding="utf-8", errors="replace") as fh:
            html = fh.read()

        manifest_match = MANIFEST_RE.search(html)
        if not manifest_match:
            die(2, f"{path} carries no __bundler/manifest")
        template_match = TEMPLATE_RE.search(html)

        if args.check:
            probe = {
                "artifact": os.path.abspath(path),
                "is_claude_design_bundle": True,
                "assets": len(json.loads(manifest_match.group(1))),
                "has_template": bool(template_match),
            }
            if template_match:
                tpl = json.loads(template_match.group(1))
                probe["bundle_shape"] = (
                    "dc-runtime" if "data-dc-script" in tpl or "text/x-dc" in tpl
                    else "babel-modules" if 'type="text/babel"' in tpl
                    else "unknown"
                )
            print(json.dumps(probe, indent=2))
            return

        if not args.out:
            die(3, "--out is required unless --check is passed")
        try:
            manifest = json.loads(manifest_match.group(1))
        except json.JSONDecodeError as exc:
            die(3, f"manifest is not valid JSON: {exc}")
        if not template_match:
            die(3, "artifact has a manifest but no __bundler/template; "
                   "load order and roles cannot be recovered")
        try:
            template = json.loads(template_match.group(1))
        except json.JSONDecodeError as exc:
            die(3, f"template is not a valid JSON string: {exc}")

        out = os.path.abspath(args.out)
        for sub in ("app", "vendor", "assets/fonts", "assets/other", "styles"):
            os.makedirs(os.path.join(out, sub), exist_ok=True)

        # --- Walk the template's script tags: they declare role AND load order.
        records: list[dict] = []
        shape: str | None = None
        order = 0
        used_names: set[str] = set()
        entry_written = False
        rewrites: dict[str, str] = {}

        for attr_text, inline in SCRIPT_TAG_RE.findall(template):
            attrs = dict(ATTR_RE.findall(attr_text))
            src = attrs.get("src")
            stype = (attrs.get("type") or "").lower()
            is_app_script = stype in APP_SCRIPT_TYPES or "data-dc-script" in attrs
            if stype == "text/x-dc" or "data-dc-script" in attrs:
                shape = "dc-runtime"
            elif stype in ("text/babel", "text/jsx"):
                shape = shape or "babel-modules"

            if src is None:
                body = inline.strip()
                if not body:
                    continue
                order += 1
                if stype == "text/x-dc" or "data-dc-script" in attrs:
                    name = "component.jsx"
                elif is_app_script and not entry_written:
                    name = "entry.jsx"
                    entry_written = True
                elif is_app_script:
                    name = f"inline-{order:02d}.jsx"
                else:
                    name = f"inline-{order:02d}.js"
                rel = os.path.join("app" if is_app_script else "vendor", name)
                with open(os.path.join(out, rel), "w", encoding="utf-8") as fh:
                    fh.write(body)
                records.append({
                    "order": order, "uuid": None,
                    "role": "app" if is_app_script else "vendor-inline",
                    "mime": "text/jsx" if is_app_script else "text/javascript",
                    "path": rel, "bytes": len(body.encode()),
                    "sha256": hashlib.sha256(body.encode()).hexdigest(),
                    "declared_name": None, "banner": None, "inline": True,
                })
                continue

            entry = manifest.get(src)
            if entry is None:
                continue
            data = decode_asset(entry)
            text = data.decode("utf-8", errors="replace")
            mime = entry.get("mime", "application/javascript")
            ext = EXT_BY_MIME.get(mime, ".js")
            order += 1

            # Role is declared by the template, never guessed: Claude Design
            # compiles app source through in-browser Babel, so every
            # type="text/babel" script is app source and every plain
            # <script src> is a vendor library.
            role = "app" if is_app_script else "vendor"
            base, declared, banner = guess_name(
                text, f"module-{order:02d}{ext}" if is_app_script else f"lib-{order:02d}{ext}"
            )

            if not os.path.splitext(base)[1]:
                base += ext
            base = f"{order:02d}-{base}" if role == "app" else base
            while base in used_names:
                base = f"x-{base}"
            used_names.add(base)

            rel = os.path.join("app" if role == "app" else "vendor", base)
            with open(os.path.join(out, rel), "w", encoding="utf-8") as fh:
                fh.write(text)
            rewrites[src] = rel
            records.append({
                "order": order, "uuid": src, "role": role, "mime": mime,
                "path": rel, "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "declared_name": declared, "banner": banner, "inline": False,
            })

        # --- Everything the template did not reference by a <script src>: fonts and
        #     images pulled from CSS, plus libraries the runtime loads dynamically.
        #     Nothing in the manifest is ever silently discarded.
        for uuid, entry in manifest.items():
            if uuid in rewrites:
                continue
            mime = entry.get("mime", "")
            data = decode_asset(entry)
            if mime.startswith("text/") or "javascript" in mime:
                # Unreferenced code. Usually a library the runtime loads itself, but it
                # could be app source in a shape we have not seen -- so keep it, and
                # label it for what it is rather than assuming.
                text = data.decode("utf-8", errors="replace")
                base, declared, banner = guess_name(text, f"unreferenced-{uuid[:8]}.js")
                rel = os.path.join("vendor", base)
                with open(os.path.join(out, rel), "w", encoding="utf-8") as fh:
                    fh.write(text)
                rewrites[uuid] = rel
                records.append({
                    "order": None, "uuid": uuid, "role": "vendor-unreferenced",
                    "mime": mime, "path": rel, "bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "declared_name": declared, "banner": banner, "inline": False,
                })
                continue
            ext = EXT_BY_MIME.get(mime, "." + (mime.split("/")[-1] or "bin"))
            sub = "assets/fonts" if mime.startswith("font/") else "assets/other"
            base = f"{uuid[:8]}{ext}"
            rel = os.path.join(sub, base)
            with open(os.path.join(out, rel), "wb") as fh:
                fh.write(data)
            rewrites[uuid] = rel
            records.append({
                "order": None, "uuid": uuid, "role": "asset", "mime": mime,
                "path": rel, "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "declared_name": None, "banner": None, "inline": False,
            })

        # --- Shell + styles. UUID srcs are rewritten to the extracted paths so
        #     the shell is readable and the token CSS is greppable on its own.
        shell = template
        for uuid, rel in rewrites.items():
            shell = shell.replace(uuid, rel)
        with open(os.path.join(out, "shell.html"), "w", encoding="utf-8") as fh:
            fh.write(shell)

        styles = STYLE_RE.findall(template)
        style_files = []
        for i, css in enumerate(styles, 1):
            rel = os.path.join("styles", f"style-{i:02d}.css")
            with open(os.path.join(out, rel), "w", encoding="utf-8") as fh:
                fh.write(css.strip())
            style_files.append({"path": rel, "bytes": len(css.encode()),
                                "custom_properties": len(re.findall(r'^\s*--[\w-]+\s*:', css, re.M))})

        title = re.search(r"<title>(.*?)</title>", template, re.S)
        extras = {kind: body for kind, body in SECTION_RE.findall(html)}

        index = {
            "generated_by": "extract_design_bundle.py",
            "artifact": os.path.abspath(path),
            "artifact_sha256": hashlib.sha256(html.encode()).hexdigest(),
            "title": (title.group(1).strip() if title else None),
            "bundle_shape": shape or "unknown",
            "unwritten_manifest_entries": [u for u in manifest if u not in rewrites],
            "counts": {
                "app_modules": sum(1 for r in records if r["role"] == "app"),
                "vendor": sum(1 for r in records if r["role"].startswith("vendor")),
                "vendor_unreferenced": sum(1 for r in records if r["role"] == "vendor-unreferenced"),
                "assets": sum(1 for r in records if r["role"] == "asset"),
                "manifest_entries": len(manifest),
            },
            "styles": style_files,
            "modules": sorted(records, key=lambda r: (r["order"] is None, r["order"] or 0)),
            "ext_resources": extras.get("ext_resources"),
            "page_order": extras.get("page_order"),
        }
        with open(os.path.join(out, "index.json"), "w", encoding="utf-8") as fh:
            json.dump(index, fh, indent=2)

        missed = index["unwritten_manifest_entries"]
        if missed:
            sys.stderr.write(
                f"warning: {len(missed)} manifest entries were not written: {missed}\n"
            )

        if index["counts"]["app_modules"] == 0:
            sys.stderr.write(
                "warning: no app source found in the template. This artifact uses an "
                "unrecognized Claude Design shape; module roles and load order could not "
                "be recovered. Treat every module as unclassified and say so.\n"
            )

        if not args.quiet:
            c = index["counts"]
            print(f"shape: {index['bundle_shape']} -- extracted {c['app_modules']} app modules, "
                  f"{c['vendor']} vendor, {c['assets']} assets, "
                  f"{len(style_files)} stylesheets -> {out}")
            for r in index["modules"]:
                if r["role"] == "app":
                    hint = f"  -- {r['banner']}" if r.get("banner") else ""
                    print(f"  {str(r['order']).rjust(2)}  {r['path']}  {r['bytes']}B{hint}")


if __name__ == "__main__":
    main()
