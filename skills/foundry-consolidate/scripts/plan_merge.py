#!/usr/bin/env python3
"""Library-consolidation planner: diff another @foundry/ui library against foundry-base.

The base is a convergence point for multiple Foundry libraries. This inventories an
incoming library (its barrel + component files) and diffs every component against the
base's foundry.index.json, bucketing each into:

  - reuse-canon   : exact match to a base CANON component -> drop the incoming copy, use canon
  - reuse-app     : exact match to a base app component    -> already covered in that app section
  - reconcile     : close-but-not-exact match to canon     -> confirm: reuse/extend canon, or promote with a distinct name
  - promote-canon : net-new AND primitive-shaped           -> add to base canon/ (enriches the shared system)
  - app-new       : net-new AND product-specific           -> add under apps/<lib>/

Populates `similar_to` links so the base index records the dedup lineage. This is a
heuristic — the consolidate skill confirms `reconcile`/`promote-canon` with the user
before mutating the base.

    python3 plan_merge.py --incoming <path/to/other/packages/ui> --index <base foundry.index.json> --lib scope
"""
import argparse
import json
import os
import re


def tokens(name):
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", name)
    s = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", s)
    return [t.lower() for t in re.split(r"[^A-Za-z0-9]+", s) if t]


def norm(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())


def overlap(a, b):
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / min(len(sa), len(sb))


# tier hint from the incoming barrel path's first segment
TIER_HINT = {"foundations": "foundation", "foundation": "foundation", "base": "primitive",
             "primitives": "primitive", "primitive": "primitive", "stats": "primitive",
             "controls": "primitive", "forms": "primitive", "composites": "app",
             "composite": "app", "application": "app", "pages": "app", "page": "app"}


def find_barrel(incoming):
    for cand in ("src/index.ts", "index.ts", "packages/ui/src/index.ts"):
        p = os.path.join(incoming, cand)
        if os.path.exists(p):
            return p
    raise SystemExit(f"no barrel (index.ts) found under {incoming}")


def parse_barrel(barrel):
    text = open(barrel).read()
    out = {}  # name -> relpath
    for m in re.finditer(r"export\s+(type\s+)?\{([\s\S]*?)\}\s*from\s*[\"'](\.[^\"']+)[\"']", text):
        if m.group(1):
            continue  # skip type-only lines for the component list
        rel = m.group(3)
        for raw in m.group(2).split(","):
            nm = raw.replace("type ", "").strip()
            if not nm:
                continue
            nm = nm.split(" as ")[-1].strip()
            if re.match(r"^[A-Z]", nm) and nm != nm.upper():  # PascalCase component-ish
                out.setdefault(nm, rel)
    return out


def first_doc(text, name):
    m = re.search(r"/\*\*([\s\S]*?)\*/\s*(?:export\s+)?(?:const|function|class)\s+" + re.escape(name), text)
    block = m.group(1) if m else (re.search(r"/\*\*([\s\S]*?)\*/", text) or [None, ""])[1] if re.search(r"/\*\*", text) else ""
    for line in (block or "").split("\n"):
        line = re.sub(r"^\s*\*\s?", "", line).strip()
        if line:
            return re.sub(r"\s+", " ", line)
    return ""


def keys_under(text, label):
    m = re.search(label + r":\s*\{([\s\S]*?)\n\s*\}", text)
    if not m:
        return []
    return list(dict.fromkeys(re.findall(r"^\s{2,}([A-Za-z_]\w*)\s*:", m.group(1), re.M)))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--incoming", required=True, help="path to the incoming library (its ui package or repo root)")
    ap.add_argument("--index", required=True, help="base foundry.index.json")
    ap.add_argument("--lib", default="lib", help="slug for the incoming library (provenance + app target)")
    ap.add_argument("--out", help="write plan JSON here (default stdout)")
    args = ap.parse_args()

    base = json.load(open(args.index))
    base_by_norm = {norm(c["name"]): c for c in base["components"]}
    base_idx = [{"name": c["name"], "tokens": set(tokens(c["name"])) | set(c.get("tags", [])),
                 "status": c["status"], "tier": c["tier"], "section": c["section"], "story": c.get("story")}
                for c in base["components"]]

    barrel = find_barrel(args.incoming)
    src_root = os.path.dirname(barrel)
    comps = parse_barrel(barrel)

    buckets = {"reuse-canon": [], "reuse-app": [], "reconcile": [], "promote-canon": [], "app-new": []}

    for name, rel in sorted(comps.items()):
        seg = rel.strip("./").split("/")[0]
        tier_hint = TIER_HINT.get(seg, "app")
        # load the component file for detail (best-effort)
        fpath = None
        for ext in (".tsx", ".ts"):
            p = os.path.join(src_root, rel[2:] + ext) if rel.startswith("./") else os.path.join(src_root, rel + ext)
            if os.path.exists(p):
                fpath = p
                break
        text = open(fpath).read() if fpath else ""
        detail = {
            "name": name, "incoming_path": os.path.relpath(fpath, args.incoming) if fpath else rel,
            "tier_hint": tier_hint,
            "description": first_doc(text, name) if text else "",
            "variants": keys_under(text, "variants") if text else [],
        }

        exact = base_by_norm.get(norm(name))
        if exact:
            entry = {**detail, "matches": exact["name"], "base_section": exact["section"]}
            (buckets["reuse-canon"] if exact["status"] == "canon" else buckets["reuse-app"]).append(entry)
            continue

        ct = tokens(name)
        ranked = sorted(({"name": c["name"], "score": round(overlap(ct, c["tokens"]), 2),
                          "status": c["status"], "section": c["section"]} for c in base_idx),
                        key=lambda x: -x["score"])
        near = [r for r in ranked if r["score"] >= 0.5][:3]
        if near and near[0]["score"] >= 0.6:
            buckets["reconcile"].append({**detail, "similar_to": near,
                                         "hint": "confirm: reuse/extend the base match, or promote with a distinct name"})
        elif tier_hint in ("foundation", "primitive"):
            buckets["promote-canon"].append({**detail, "similar_to": near,
                                             "target": f"packages/ui/src/components/canon/primitives/{kebab(name)}.tsx",
                                             "hint": "net-new reusable primitive -> add to base canon"})
        else:
            buckets["app-new"].append({**detail, "similar_to": near,
                                       "target": f"packages/ui/src/components/apps/{args.lib}/{kebab(name)}.tsx"})

    plan = {
        "incomingLib": args.lib,
        "incoming": args.incoming,
        "provenance": args.lib,
        "summary": {k: len(v) for k, v in buckets.items()},
        "componentsScanned": len(comps),
        **buckets,
        "guidance": "reuse-canon/reuse-app: drop the incoming copy. reconcile: confirm each with the user (prefer reuse/extend canon). promote-canon: retheme to base tokens (component-porter, canon golden ref) and add to canon/. app-new: add under apps/<lib>/. Set provenance + similar_to in the index; run `bun run index` after.",
    }
    text = json.dumps(plan, indent=2)
    if args.out:
        open(args.out, "w").write(text + "\n")
        print("wrote", args.out, "-", {k: len(v) for k, v in buckets.items()})
    else:
        print(text)


def kebab(name):
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "-", name).lower()


if __name__ == "__main__":
    main()
