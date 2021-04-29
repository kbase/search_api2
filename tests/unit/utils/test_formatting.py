import unittest

from src.utils.formatting import iso8601_to_epoch_ms


class UtilsFormattingTest(unittest.TestCase):
    def test_iso8601_to_epoch_ms_valid(self):
        cases = [
            {
                'input': '1970-01-01T00:00:00Z',
                'expected': 0
            }
        ]
        for case in cases:
            self.assertEqual(iso8601_to_epoch_ms(case['input']), case['expected'])
