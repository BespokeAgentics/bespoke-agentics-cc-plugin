import unittest

from reportgen.cli import main


class TestCli(unittest.TestCase):
    def test_main_renders_escaped(self):
        self.assertIn("<h1>T</h1>", main("T", "a < b"))
        self.assertIn("a &lt; b", main("T", "a < b"))
