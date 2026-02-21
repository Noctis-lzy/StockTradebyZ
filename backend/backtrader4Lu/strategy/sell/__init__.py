from .base import SellStrategy
from .close_below_duokong import CloseBelowDuokongSellStrategy
from .standard_top_windmill import StandardTopWindmillSellStrategy
from .suspected_top_windmill import SuspectedTopWindmillSellStrategy

__all__ = [
    'SellStrategy',
    'CloseBelowDuokongSellStrategy',
    'StandardTopWindmillSellStrategy',
    'SuspectedTopWindmillSellStrategy'
]
