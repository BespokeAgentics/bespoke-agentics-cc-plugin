#!/usr/bin/env python3
"""The consultation hook must read the answer, not the thinking block.

Current Claude models think by default and return a `thinking` block first. The
template used to read `content[0]["text"]`, which is a KeyError on a thinking
block; the hook degrades silently, so the session started with no second opinion
and nothing said why. These tests pin the response shapes the Anthropic branch
has to handle.

  python3 skills/session-hooks/tests/test_start_ai_consultation.py
"""

from __future__ import annotations

import importlib.util
import io
import json
import unittest
from pathlib import Path
from unittest import mock

TEMPLATE = Path(__file__).resolve().parents[1] / "templates" / "start-ai-consultation.py"
spec = importlib.util.spec_from_file_location("consult", TEMPLATE)
consult = importlib.util.module_from_spec(spec)
spec.loader.exec_module(consult)


def respond(body: dict):
    resp = mock.MagicMock()
    resp.__enter__.return_value = io.BytesIO(json.dumps(body).encode())
    return resp


class TestAnthropicBranch(unittest.TestCase):
    def call(self, body: dict, max_tokens: int = 400):
        with mock.patch.object(consult.urllib.request, "urlopen", return_value=respond(body)) as urlopen, \
                mock.patch.object(consult, "warn"):
            out = consult.call_anthropic("claude-opus-5", "key", "sys", "user", max_tokens)
        sent = json.loads(urlopen.call_args.args[0].data)
        return out, sent

    def test_thinking_block_first_returns_the_text_block(self):
        out, _ = self.call({"stop_reason": "end_turn", "content": [
            {"type": "thinking", "thinking": "", "signature": "s"},
            {"type": "text", "text": "framing"},
        ]})
        self.assertEqual(out, "framing")

    def test_text_only_response_still_works(self):
        out, _ = self.call({"stop_reason": "end_turn", "content": [{"type": "text", "text": "framing"}]})
        self.assertEqual(out, "framing")

    def test_refusal_returns_none(self):
        out, _ = self.call({"stop_reason": "refusal", "content": []})
        self.assertIsNone(out)

    def test_no_text_block_returns_none(self):
        out, _ = self.call({"stop_reason": "max_tokens", "content": [{"type": "thinking", "thinking": ""}]})
        self.assertIsNone(out)

    def test_max_tokens_leaves_room_for_thinking(self):
        _, sent = self.call({"stop_reason": "end_turn", "content": [{"type": "text", "text": "x"}]}, max_tokens=400)
        self.assertGreaterEqual(sent["max_tokens"], 4000)
        _, sent = self.call({"stop_reason": "end_turn", "content": [{"type": "text", "text": "x"}]}, max_tokens=8000)
        self.assertEqual(sent["max_tokens"], 8000)


if __name__ == "__main__":
    unittest.main()
