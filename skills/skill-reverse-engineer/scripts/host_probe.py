#!/usr/bin/env python3
"""Bounded candidate enumerator for a host project.

Usage: host_probe.py <host-root> [--json]

Enumerates *candidates* for host grounding — manifests, lockfiles, schema
sources, wiki vaults, CI config, and data-store evidence — by existence and
name patterns only. It is deliberately NOT a stack detector: interpretation
(what the stack is, which facts are stable, what deserves materialization)
is the caller's job. Output feeds the host-context.json contract in
references/materialization.md.

Exit codes: 0 ok · 1 usage error.
"""

import json
import os
import re
import sys

MAX_DEPTH = 5
MAX_HITS_PER_BUCKET = 40

SKIP_DIRS = {
    "node_modules", ".git", ".hg", ".svn", "__pycache__", ".venv", "venv",
    "dist", "build", "target", ".next", ".turbo", "vendor", ".cache",
}

MANIFEST_NAMES = {
    "package.json", "pyproject.toml", "requirements.txt", "setup.py",
    "go.mod", "Cargo.toml", "composer.json", "Gemfile", "pom.xml",
    "build.gradle", "mix.exs",
}
MANIFEST_SUFFIXES = (".csproj", ".fsproj")

LOCKFILE_NAMES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lock",
    "bun.lockb", "poetry.lock", "uv.lock", "Cargo.lock", "composer.lock",
    "Gemfile.lock", "go.sum",
}

SCHEMA_DIR_NAMES = {"migrations", "migrate", "alembic", "drizzle"}
SCHEMA_FILE_PATTERNS = (
    re.compile(r"^schema\.prisma$"),
    re.compile(r"^openapi\.(json|ya?ml)$"),
    re.compile(r"^swagger\.(json|ya?ml)$"),
    re.compile(r"\.graphql$"),
    re.compile(r"\.sql$"),
)

CI_MARKERS = (".github/workflows", ".gitlab-ci.yml", ".circleci", "Jenkinsfile")

CONN_KEY = re.compile(
    r"(DATABASE_URL|_DSN|CONNECTION_STRING|REDIS_URL|MONGO(DB)?_URI|AMQP_URL|KAFKA_BROKERS)",
    re.IGNORECASE,
)


def add(bucket, item, out):
    lst = out["detected"][bucket]
    if len(lst) < MAX_HITS_PER_BUCKET:
        lst.append(item)
    else:
        out["truncated"] = True


def grep_lines(path, pattern, tag, out):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f, 1):
                if pattern.search(line):
                    out["store_evidence"].append(
                        {"path": path, "line": i, "text": line.strip()[:200], "kind": tag}
                    )
                    if len(out["store_evidence"]) >= MAX_HITS_PER_BUCKET:
                        out["truncated"] = True
                        return
    except OSError:
        pass


def main(argv):
    args = [a for a in argv[1:] if a != "--json"]
    as_json = "--json" in argv[1:]
    if len(args) != 1 or args[0] in ("-h", "--help"):
        print(__doc__.strip(), file=sys.stderr)
        return 1
    root = os.path.abspath(args[0])
    if not os.path.isdir(root):
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 1

    out = {
        "host_root": root,
        "detected": {
            "manifests": [], "lockfiles": [], "schema_sources": [],
            "wiki_vaults": [], "ci": [],
        },
        "store_evidence": [],
        "truncated": False,
    }

    for dirpath, dirs, files in os.walk(root):
        rel = os.path.relpath(dirpath, root)
        depth = 0 if rel == "." else rel.count(os.sep) + 1
        if depth >= MAX_DEPTH:
            dirs[:] = []
        dirs[:] = sorted(
            d for d in dirs
            if d not in SKIP_DIRS and not (d.startswith(".") and d != ".github")
        )

        for d in list(dirs):
            if d in SCHEMA_DIR_NAMES or (d == "migrate" and os.path.basename(dirpath) == "db"):
                add("schema_sources", os.path.join(rel, d).lstrip("./") + "/", out)

        for name in sorted(files):
            relpath = os.path.normpath(os.path.join(rel, name)).lstrip("./")
            if name in MANIFEST_NAMES or name.endswith(MANIFEST_SUFFIXES):
                add("manifests", relpath, out)
            if name in LOCKFILE_NAMES:
                add("lockfiles", relpath, out)
            if any(p.search(name) for p in SCHEMA_FILE_PATTERNS):
                add("schema_sources", relpath, out)
            if name == "SCHEMA.md" and os.path.basename(dirpath) == "_schema":
                add("wiki_vaults", relpath, out)
            # Exactly two content greps, bounded, raw evidence only:
            if name.startswith("docker-compose") and name.endswith((".yml", ".yaml")):
                grep_lines(os.path.join(dirpath, name), re.compile(r"^\s*image:"),
                           "compose-image", out)
            if name in (".env.example", ".env.sample", ".env.template"):
                grep_lines(os.path.join(dirpath, name), CONN_KEY, "connection-key", out)

    for marker in CI_MARKERS:
        if os.path.exists(os.path.join(root, marker)):
            out["detected"]["ci"].append(marker)

    if as_json:
        print(json.dumps(out, indent=2))
    else:
        print(f"host: {root}")
        for bucket, items in out["detected"].items():
            if items:
                print(f"{bucket}: {len(items)}")
                for i in items[:10]:
                    print(f"  {i}")
        if out["store_evidence"]:
            print(f"store_evidence: {len(out['store_evidence'])}")
            for ev in out["store_evidence"][:10]:
                print(f"  {ev['path']}:{ev['line']} [{ev['kind']}] {ev['text']}")
        if out["truncated"]:
            print("NOTE: output truncated at bucket caps")
        if not any(out["detected"].values()) and not out["store_evidence"]:
            print("no candidates found — likely no-host")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
