#!/usr/bin/env python3
"""The stop hook writes wiki/_log.md in the wiki's own entry format.

The wiki skills write, and wiki-status parses, `## YYYY-MM-DD — <operation> — <summary>`
headings. This hook used to append a table row, which wiki-status could not read.

  python3 skills/session-hooks/tests/test_stop_wiki_log.py
"""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "templates" / "stop-wiki-log.sh"
ENTRY = re.compile(r"^## \d{4}-\d{2}-\d{2} — session — .+$", re.M)


def run_hook(root: Path, session_id: str) -> None:
    payload = json.dumps({"session_id": session_id, "cwd": str(root)})
    subprocess.run(["bash", str(HOOK)], input=payload, text=True, cwd=root, check=True, capture_output=True)


class TestStopWikiLog(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "wiki").mkdir()
        self.log = self.root / "wiki" / "_log.md"
        self.log.write_text("# Log\n")

    def tearDown(self):
        self.tmp.cleanup()

    def test_appends_a_heading_entry_not_a_table_row(self):
        run_hook(self.root, "abc12345xyz")
        text = self.log.read_text()
        self.assertRegex(text, ENTRY)
        self.assertIn("abc12345", text)
        self.assertNotRegex(text, r"^\|", "table rows are not the wiki's log format")

    def test_writes_once_per_session_per_day(self):
        run_hook(self.root, "abc12345xyz")
        run_hook(self.root, "abc12345xyz")
        self.assertEqual(len(ENTRY.findall(self.log.read_text())), 1)

    def test_missing_log_is_a_silent_skip(self):
        self.log.unlink()
        run_hook(self.root, "abc12345xyz")
        self.assertFalse(self.log.exists())


if __name__ == "__main__":
    unittest.main()
