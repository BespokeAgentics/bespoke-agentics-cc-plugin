import unittest

from reportgen.export import export


class TestExport(unittest.TestCase):
    def test_json_format(self):
        self.assertEqual(export("ok", "json"), '{"report": "ok"}')

    def test_text_format(self):
        self.assertEqual(export("ok", "text"), "ok")
