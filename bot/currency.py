from typing import Union


class Currency(object):
    __slots__ = ('name', 'iso', 'buy', 'sell')

    def __init__(self, name: str="",
                 iso: str="",
                 sell: Union[float, int]=None,
                 buy: Union[float, int]=None) -> None:
        self.name = name
        self.iso = iso
        self.sell = sell
        self.buy = buy

    def __repr__(self) -> str:
        s = "Currency({}, {}, {}, {})"
        return s.format(self.name, self.iso, self.sell, self.buy)

    def __str__(self) -> str:
        return "<Currency {}: {} : {}>".format(self.iso,
                                               self.sell,
                                               self.buy if self.buy else "-")

    def __eq__(self, other):
        sell_equal = self.sell == other.sell
        buy_equal = self.buy == other.buy
        iso_equal = self.iso == other.iso
        return sell_equal and buy_equal and iso_equal

    def __hash__(self) -> int:
        s = self.iso + str(self.sell) + str(self.buy)
        return hash(s)

    @classmethod
    def empty_currency(cls):
        return Currency("NoValue", "", 0, 0)

