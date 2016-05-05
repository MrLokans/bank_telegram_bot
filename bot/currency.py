from typing import Union


class Currency(object):
    __slots__ = ('name', 'iso', 'buy', 'sell')

    def __init__(self, name: str="",
                 iso: str="",
                 sell: Union[float, int]=None,
                 buy: float=None) -> None:
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
