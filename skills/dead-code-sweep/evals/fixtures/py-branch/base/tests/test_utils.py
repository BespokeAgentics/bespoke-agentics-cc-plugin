import unittest

from reportgen.utils import wrap_text


class TestWrapText(unittest.TestCase):
    def test_wraps_at_width(self):
        out = wrap_text("aaa bbb ccc", 7)
        self.assertEqual(out, "aaa bbb\nccc")
