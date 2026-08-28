#!/usr/bin/env python3
"""Prove validate-marketplace.py still has teeth.

Every case below is a form that was actually authored into this repo and
shipped, or a drift the pin makes possible. A validator that passes the
good input proves nothing on its own -- zero findings is also what a blind
check reports -- so each tampered entry must FAIL for a stated reason.
"""

import json, subprocess, sys, tempfile, os
from pathlib import Path
SRC = Path('.claude-plugin/marketplace.json')
base = json.loads(SRC.read_text())

def run(mutate, label, expect):
    d = json.loads(json.dumps(base))
    for e in d['plugins']:
        if e['name'] == 'impeccable-microdots':
            mutate(e)
    f = Path(tempfile.mkdtemp()) / 'marketplace.json'
    f.write_text(json.dumps(d, indent=2))
    r = subprocess.run([sys.executable, 'scripts/validate-marketplace.py', '--file', str(f)],
                       capture_output=True, text=True)
    out = r.stdout + r.stderr
    ok = r.returncode != 0 and expect in out
    print(f"{'PASS' if ok else 'MISS'}  {label}")
    if not ok:
        print('        exit', r.returncode, '|', out.strip().replace('\n', ' | ')[:200])
    return ok

cases = [
  (lambda e: e.update(source="github:BespokeAgentics/impeccable-microdots"),
   'attempt 1: "github:owner/repo" shorthand', 'relative path only'),
  (lambda e: e.update(source={"source":"github","repo":"BespokeAgentics/impeccable-microdots"}),
   'attempt 2: github type (ssh clone)', 'SSH key'),
  (lambda e: e.update(source={"source":"git","url":"https://github.com/BespokeAgentics/impeccable-microdots.git"}),
   'attempt 3: git type (marketplace-only)', 'plugin entries reject it'),
  (lambda e: e['source'].update(sha="0"*40),
   'C3: stale / bogus pin', 'stale'),
  (lambda e: e['source'].pop('sha'),
   'C4: unpinned remote', 'no pinned sha'),
  (lambda e: e.update(version="9.9.9"),
   'C5: version drift', 'version drift'),
  (lambda e: e['source'].update(url="https://github.com/BespokeAgentics/does-not-exist-xyz.git"),
   'C2: unreachable repo', 'not reachable'),
  (lambda e: e['source'].update(url="git@github.com:BespokeAgentics/impeccable-microdots.git"),
   'C2: ssh url', 'SSH endpoint'),
]
results = [run(m, l, x) for m, l, x in cases]
print(f"\n{sum(results)}/{len(results)} tamper cases caught")
sys.exit(0 if all(results) else 1)
