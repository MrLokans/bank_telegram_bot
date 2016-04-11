import datetime
import unittest

from unittest.mock import patch

from utils import (
    get_date_arg,
    get_date_from_date_diff,
    str_from_date,
    date_diffs_for_long_diff
)


class TestUtils(unittest.TestCase):

    def test_correctly_parses_date_flag_if_present(self):
        args = ['course', 'USD', '-d10', 'test']
        self.assertEqual(get_date_arg(args), 10)

    def test_correctly_parses_date_flag_if_not_present(self):
        args = ['course', 'USD', 'test']
        self.assertEqual(get_date_arg(args), 0)

    @unittest.skip("Undefined behaviour.")
    def test_correctly_parses_multiple_date_flags(self):
        args = ['course', 'USD', 'test']
        self.assertEqual(get_date_arg(args), 0)

    @patch('datetime.datetime')
    def test_correctly_finds_diff_date(self, now_mock):
        now_date = datetime.date(year=2016, month=10, day=10)
        now_mock.now.return_value = now_date
        self.assertEqual(get_date_from_date_diff(5),
                         datetime.date(year=2016, month=10, day=5))

    def test_correctly_builds_string_from_date(self):
        d = datetime.date(year=2016, month=2, day=20)
        self.assertEqual(str_from_date(d), "20.02.2016")

    def test_correct_diff_splitting(self):
        days = 1
        self.assertEqual(date_diffs_for_long_diff(days), [0, 1])

        days = 2
        self.assertEqual(date_diffs_for_long_diff(days), [0, 1, 2])

        days = 3
        self.assertEqual(date_diffs_for_long_diff(days), [0, 1, 2, 3])

        days = 4
        self.assertEqual(date_diffs_for_long_diff(days), [0, 1, 2, 3, 4])

        days = 12
        self.assertEqual(date_diffs_for_long_diff(days),
                         [0, 2, 4, 6, 8, 10, 12])

        days = 21
        self.assertEqual(date_diffs_for_long_diff(days),
                         [0, 3, 6, 9, 12, 15, 18, 21])

        days = 11
        self.assertEqual(date_diffs_for_long_diff(days),
                         [0, 1, 2, 3, 4, 5, 6, 10])


if __name__ == '__main__':
    unittest.main()
