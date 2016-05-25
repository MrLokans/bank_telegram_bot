from typing import Union, Dict


class Currency(object):
    __slots__ = ('name', 'iso', 'buy', 'sell', 'multiplier')

    def __init__(self, name: str="",
                 iso: str="",
                 sell: Union[float, int]=None,
                 buy: Union[float, int]=None,
                 multiplier: int=1) -> None:
        self.name = name
        self.iso = iso
        self.sell = sell
        self.buy = buy
        self.multiplier = multiplier

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
        mul_equal = self.multiplier == other.multiplier
        return sell_equal and buy_equal and iso_equal and mul_equal

    def __hash__(self) -> int:
        s = self.iso + str(self.sell) + str(self.buy)
        return hash(s)

    @classmethod
    def empty_currency(cls):
        return Currency("NoValue", "", 0, 0)

    def to_dict(self) -> Dict[str, Union[str, float, int]]:
        currency_dict = {
            "name": self.name,
            "iso": self.iso,
            "buy": self.buy,
            "sell": self.sell,
            "multiplier": self.multiplier
        }
        return currency_dict

    @classmethod
    def from_dict(cls, d: Dict[str, Union[str, float, int]]):
        return cls(**d)
