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


def check(label, ok, detail=''):
    print(f"{'PASS' if ok else 'MISS'}  {label}")
    if not ok and detail:
        print(f"        {detail}")
    return ok


def load_validator():
    import importlib.util
    spec = importlib.util.spec_from_file_location('vm', 'scripts/validate-marketplace.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# The reachability probe once answered from the developer's macOS keychain:
# Apple Git's system gitconfig sets credential.helper=osxkeychain and
# GIT_CONFIG_SYSTEM=/dev/null does not suppress it, so a PRIVATE repo
# validated green locally and failed in CI on the same commit.
vm = load_validator()
helpers = vm.git(['config', '--get-all', 'credential.helper']).stdout.strip()
results.append(check(
    'probe is anonymous: no credential helper survives',
    helpers == '',
    f'git still resolves credential.helper={helpers!r} under bare_git_env()',
))
results.append(check(
    'bare_git_env sets GIT_CONFIG_NOSYSTEM',
    vm.bare_git_env().get('GIT_CONFIG_NOSYSTEM') == '1',
))

# An entry whose manifest declared no skills path produced no output at all,
# yet the summary counted it among the entries it called install-clean.
vm2 = load_validator()
vm2.check_remote = lambda *a, **k: None          # a check that reports nothing
f = Path(tempfile.mkdtemp()) / 'marketplace.json'
f.write_text(json.dumps({'plugins': [
    {'name': 'silent', 'version': '1.0.0',
     'source': {'source': 'url', 'url': 'https://example.invalid/x.git', 'sha': '0' * 40}},
]}))
vm2.MARKETPLACE = f
rc = vm2.main()
results.append(check(
    'an entry that reports nothing is a failure, not a pass',
    rc == 1 and any('silent pass' in e for e in vm2.errors),
    f'exit {rc}, errors={vm2.errors}',
))

print(f"\n{sum(results)}/{len(results)} tamper cases caught")
sys.exit(0 if all(results) else 1)
