import unittest

from reportgen.render import render_html_legacy


class TestRenderLegacy(unittest.TestCase):
    def test_wraps_and_renders(self):
        out = render_html_legacy("Hi", "word " * 30, width=20)
        self.assertIn("<h1>Hi</h1>", out)
        self.assertIn("\n", out)
