import datetime
import unittest


from bot.exceptions import BotParserLookupError
from bot.currency import Currency
from bot.utils import (
    get_parser,
    get_parser_classes
)


class TestParserListObtaining(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.EXISTING_PARSER_NAME = 'nbrb'
        cls.NON_EXISTING_PARSER_NAME = 'NONEXISTING'
        cls.TODAY = datetime.datetime.utcnow().date()

    def _validate_currency(self, currency, iso_code: str=''):
        self.assertTrue(isinstance(currency, Currency))
        self.assertTrue(isinstance(currency.sell, float))
        self.assertTrue(isinstance(currency.buy, float))
        if iso_code:
            self.assertEqual(currency.iso, iso_code)
        self.assertFalse(currency.is_empty())

    def _regression_test_for_parser(self, parser_name: str):
        parser = get_parser(parser_name)()
        usd_currency = parser.get_currency('USD', date=self.TODAY)

        self._validate_currency(usd_currency, iso_code='USD')

        currencies = parser.get_all_currencies(date=self.TODAY)
        [self._validate_currency(c) for c in currencies]

    def test_returns_list_of_parser_classes(self):
        parser_classes = get_parser_classes()

        self.assertTrue(len(parser_classes) > 0)

    def test_getting_existing_parser_returns_appropriate_class(self):
        parser_cls = get_parser(self.EXISTING_PARSER_NAME)

        self.assertEqual(parser_cls.short_name, self.EXISTING_PARSER_NAME)

    def test_getting_non_existing_parser_raises_error(self):
        with self.assertRaises(BotParserLookupError):
            get_parser(self.NON_EXISTING_PARSER_NAME)

    # def test_NBRB_parser(self):
    #     self._regression_test_for_parser('nbrb')

    # def test_BGP_parser(self):
    #     self._regression_test_for_parser('bgp')

    def test_ALFABANK_parser(self):
        self._regression_test_for_parser('alfabank')

    # def test_PRIOBRBANK_parser(self):
    #     self._regression_test_for_parser('prbp')

    # def test_BELWEB_parser(self):
    #     self._regression_test_for_parser('bwb')
