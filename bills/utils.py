from typing import Optional

from forex_python.converter import CurrencyRates
from forex_python.bitcoin import BtcConverter

def convert_value(value: Optional[float], from_cur: Optional[str], to_cur: Optional[str]) -> Optional[float]:
    """
    Convert value from one currency to other currency
    :param value: Value
    :param from_cur: Base currency
    :param to_cur: Converted currency
    :return: Converted value
    """
    converter = CurrencyRates()
    converter_btc = BtcConverter()

    if from_cur == to_cur:
        return value

    if from_cur == "BTC":
        raise TypeError("Not available convert from BTC")

    if to_cur == "BTC":
        return converter_btc.convert_to_btc(value, from_cur)

    return converter.convert(from_cur, to_cur, value)