#!/usr/bin/env python3
"""Reuse-first port planner: diff a new design against the foundry-base index.

Given analyze_zip.py's analysis.json (the new design's component inventory) and the
base's foundry.index.json, decide for each design component whether to REUSE an
existing canon/app component, treat it as AMBIGUOUS (a close-but-not-exact match to
confirm), or PORT it as net-new. Screens become pages.

The point is to never re-port what the base already provides. This is a heuristic —
the skill confirms ambiguous matches with the user before wiring them.

    python3 plan_ports.py --analysis analysis.json --index foundry.index.json --app ledger
"""
import argparse
import json
import re


def tokens(name):
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", name)
    s = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", s)
    return [t.lower() for t in re.split(r"[^A-Za-z0-9]+", s) if t]


def norm(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())


def overlap(a, b):
    """Overlap coefficient: |A∩B| / min(|A|,|B|)."""
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / min(len(sa), len(sb))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--analysis", required=True, help="analyze_zip.py output for the new design")
    ap.add_argument("--index", required=True, help="foundry-base foundry.index.json")
    ap.add_argument("--app", default="app", help="new app slug (for the port target path)")
    ap.add_argument("--out", help="write plan JSON here (default: stdout)")
    args = ap.parse_args()

    analysis = json.load(open(args.analysis))
    index = json.load(open(args.index))

    idx = []
    for c in index["components"]:
        idx.append({
            "name": c["name"],
            "tier": c["tier"],
            "status": c["status"],
            "section": c["section"],
            "story": c.get("story"),
            "tokens": set(tokens(c["name"])) | set(c.get("tags", [])),
            "norm": norm(c["name"]),
        })
    idx_by_norm = {c["norm"]: c for c in idx}

    screens = set(analysis.get("screens", []))
    reuse, ambiguous, port = [], [], []

    for comp in analysis.get("components", []):
        name = comp["name"]
        if name == "App" or comp.get("screen") or name in screens:
            continue  # screens -> pages, handled below

        # exact name match first
        hit = idx_by_norm.get(norm(name))
        if hit:
            reuse.append({
                "design": name, "use": hit["name"], "tier": hit["tier"],
                "status": hit["status"], "story": hit["story"],
                "match": "exact-name",
            })
            continue

        # otherwise rank by token overlap
        ct = tokens(name)
        ranked = sorted(
            ({"name": c["name"], "score": round(overlap(ct, c["tokens"]), 2),
              "tier": c["tier"], "status": c["status"], "story": c["story"]} for c in idx),
            key=lambda x: -x["score"],
        )
        top = [r for r in ranked if r["score"] >= 0.5][:3]
        if top and top[0]["score"] >= 0.5:
            ambiguous.append({"design": name, "candidates": top,
                              "hint": "confirm reuse/extend vs port"})
        else:
            port.append({
                "design": name,
                "reason": "no canon match",
                "role": comp.get("role"),
                "props": [p["name"] for p in comp.get("props", [])],
                "out_path": f"packages/ui/src/components/apps/{args.app}/{re.sub(r'(?<=[a-z0-9])(?=[A-Z])','-',name).lower()}.tsx",
            })

    pages = [s for s in analysis.get("screens", []) if s != "App"]

    plan = {
        "app": args.app,
        "summary": {
            "designComponents": len([c for c in analysis.get("components", []) if c["name"] != "App" and not c.get("screen")]),
            "reuse": len(reuse), "ambiguous": len(ambiguous), "port": len(port), "pages": len(pages),
        },
        "reuse": reuse,
        "ambiguous": ambiguous,
        "port": port,
        "pages": pages,
        "guidance": "Wire `reuse` from @foundry/ui. Confirm `ambiguous` with the user (prefer reuse/extend canon). Dispatch component-porter for each `port` item into apps/<app>/. Build `pages` as Apps/<App>/Pages stories. Run `bun run index` after porting.",
    }

    text = json.dumps(plan, indent=2)
    if args.out:
        open(args.out, "w").write(text + "\n")
        print(f"wrote {args.out}: reuse={plan['summary']['reuse']} ambiguous={plan['summary']['ambiguous']} port={plan['summary']['port']} pages={plan['summary']['pages']}")
    else:
        print(text)


if __name__ == "__main__":
    main()
