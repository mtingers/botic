"""Simple trader"""
import time
from decimal import Decimal
from .base import BaseTrader
from ..util import str2bool

class Simple(BaseTrader):
    """Simple trader"""
    # pylint: disable=too-many-instance-attributes
    def __init__(self, config) -> None:
        super().__init__(config)
        print('start')
        self.usd_decimal_places = None
        self.size_decimal_places = None
        self.current_price = None
        self.current_price_target = None
        self.taker_fee = None
        self.maker_fee = None
        self.usd_volume = None
        self.product_info = None
        self.current_price_increase = None
        self.wallet = None

    def configure(self) -> None:
        print('configure_trader_custom')
        self.max_outstanding_sells = int(self.max_outstanding_sells)
        self.max_buys_per_hour = int(self.max_buys_per_hour)
        self.sell_target = Decimal(self.sell_target)
        self.sell_barrier = Decimal(self.sell_barrier)
        self.buy_percent = Decimal(self.buy_percent)
        self.buy_max = Decimal(self.buy_max)
        self.buy_min = Decimal(self.buy_min)
        self.stoploss_enable = str2bool(self.stoploss_enable)
        self.stoploss_percent = Decimal(self.stoploss_percent)
        self.stoploss_seconds = int(self.stoploss_seconds)
        self.stoploss_strategy = str(self.stoploss_strategy)

    def run_trading_algorithm(self) -> None:
        self.logit('run_trading_algorithm')
        self._get_all()

    def _get_all(self) -> None:
        time.sleep(0.5)
        self.wallet = self.exchange.get_usd_wallet()
        self.product_info = self.exchange.get_product_info()
        time.sleep(0.5)
        self.current_price = self.exchange.get_price()
        self.maker_fee, self.taker_fee, self.usd_volume = self.exchange.get_fees()
        self.size_decimal_places, self.usd_decimal_places = self.exchange.get_precisions()
        self._get_current_price_target()
        #self.can_buy = self._check_if_can_buy()
        print(self.current_price_target)

    def _get_current_price_target(self) -> Decimal:
        current_percent_increase = (self.maker_fee + self.taker_fee) + (self.sell_target / 100)
        self.current_price_target = round(
            self.current_price * current_percent_increase + self.current_price,
            self.usd_decimal_places
        )
        self.current_price_increase = self.current_price * current_percent_increase
        return self.current_price_target
