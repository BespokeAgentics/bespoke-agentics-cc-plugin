import unittest

from reportgen.render import render_html


class TestRenderHtml(unittest.TestCase):
    def test_escapes_and_renders(self):
        out = render_html("A & B", "x < y")
        self.assertIn("<h1>A &amp; B</h1>", out)
        self.assertIn("x &lt; y", out)
