import unittest

from reportgen.cli import main


class TestCli(unittest.TestCase):
    def test_main_renders(self):
        self.assertIn("<h1>T</h1>", main("T", "body"))
