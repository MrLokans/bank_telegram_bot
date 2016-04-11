import datetime
import unittest

from unittest.mock import patch

from utils import get_date_arg, get_date_from_date_diff, str_from_date


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

if __name__ == '__main__':
    unittest.main()
