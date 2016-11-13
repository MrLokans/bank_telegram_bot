import datetime
import unittest

from bot.utils import (
    get_date_arg,
    get_date_from_date_diff,
    date_diffs_for_long_diff,
    sort_currencies
)

from bot.currency import Currency


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

    def test_correctly_finds_diff_date(self,):
        today = datetime.date(year=2016, month=10, day=10)
        self.assertEqual(get_date_from_date_diff(5, today),
                         datetime.date(year=2016, month=10, day=5))

    def test_correct_diff_splitting(self):

        max_diff = 30
        for i in range(1, max_diff):
            self.assertEqual(date_diffs_for_long_diff(i),
                             list(range(i + 1)))
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

    def test_generic_currencies_sorted_correctly(self):
        c1 = Currency(iso="PLZ", buy=20, sell=30)
        c2 = Currency(iso="AUD", buy=20, sell=30)
        c3 = Currency(iso="BLZ", buy=20, sell=30)
        c4 = Currency(iso="ZLT", buy=20, sell=30)
        self.assertEqual(sort_currencies([c1, c2, c3, c4]), [c2, c3, c1, c4])

    def test_specific_currencies_sorted_correctly(self):
        c1 = Currency(iso="RUB", buy=20, sell=30)
        c2 = Currency(iso="USD", buy=20, sell=30)
        c3 = Currency(iso="BLZ", buy=20, sell=30)
        c4 = Currency(iso="ZLT", buy=20, sell=30)
        self.assertEqual(sort_currencies([c1, c2, c3, c4]), [c2, c1, c3, c4])

if __name__ == '__main__':
    unittest.main()
