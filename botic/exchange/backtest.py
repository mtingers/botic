"""Backtest exchange module

- Currently handles BTC-USD for the ProductInfo config.
- TODO: Add more

"""
import time
import configparser
import typing as t
from .base import BaseExchange, ProductInfo, Decimal

class Backtest(BaseExchange):
    """Backtest"""
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=no-member
    def __init__(self, config: configparser.ConfigParser) -> None:
        super().__init__(config)
        self.usd_decimal_places = 2
        self.size_decimal_places = 8
        self._last_call = time.time()
        self._wallet = Decimal('10000.00')
        self._orders = []
        self._price_data = []
        self._price_idx = 0

        self._product_info_config = {
            'id':self.coin,
            'display_name':self.coin,
            'base_currency':self.coin.split('-')[0],
            'quote_currency':'USD',
            'base_increment':Decimal('0.00000001'),
            'quote_increment':Decimal('0.01000000'),
            'base_min_size':Decimal('0.00100000'),
            'base_max_size':Decimal('280.00000000'),
            'min_market_funds':5,
            'max_market_funds':1000000,
            'status':'online',
            'status_message':'',
            'cancel_only':False,
            'limit_only':False,
            'post_only':False,
            'trading_disabled':False,
            'margin_enabled':False,
        }
        if self.coin != 'BTC-USD':
            raise Exception('Currently only handles BTC-USD')

    def authenticate(self):
        return None

    def get_price(self) -> Decimal:
        price = self._price_data[self._price_idx]
        self._price_idx += 1
        if len(self._price_data) <= self._price_idx:
            raise Exception('No more price data')
        return Decimal(price)

    def get_precisions(self) -> ProductInfo:
        product_info = self.get_product_info()
        base_increment = '%.12f' % (product_info.base_increment)
        quote_increment = '%.12f' % (product_info.quote_increment)
        self.size_decimal_places = base_increment.split('1')[0].count('0')
        self.usd_decimal_places = quote_increment.split('1')[0].count('0')
        return (self.size_decimal_places, self.usd_decimal_places)

    def get_product_info(self) -> ProductInfo:
        product_info = ProductInfo(self._product_info_config)
        return product_info

    def get_usd_wallet(self) -> Decimal:
        return self.wallet

    def get_open_sells(self) -> t.List[t.Mapping[str, Decimal]]:
        return self.orders

    def get_fees(self) -> t.Tuple[Decimal, Decimal, Decimal]:
        (maker_fee, taker_fee, usd_volume) = (Decimal('0.005'), Decimal('0.005'), Decimal('1'))
        return (maker_fee, taker_fee, usd_volume)

    def buy_limit(self, price: Decimal, size: Decimal) -> dict:
        #fixed_price = str(round(Decimal(price), self.usd_decimal_places))
        #fixed_size = str(round(Decimal(size), self.size_decimal_places))
        return {}

    def buy_market(self, funds: Decimal) -> dict:
        funds = str(round(Decimal(funds), self.usd_decimal_places))
        self.logit('buy_market: funds:{}'.format(funds))
        return {}

    def sell_limit(self, price: Decimal, size: Decimal) -> dict:
        fixed_price = str(round(Decimal(price), self.usd_decimal_places))
        fixed_size = str(round(Decimal(size), self.size_decimal_places))
        self.logit('sell_limit: price:{} size:{}'.format(fixed_price, fixed_size))
        return {}

    def sell_market(self, size: Decimal) -> dict:
        fixed_size = str(round(Decimal(size), self.size_decimal_places))
        self.logit('sell_market: size:{}'.format(fixed_size))
        return {}

    def cancel(self, order_id: str) -> bool:
        return {}

    def get_order(self, order_id: str) -> dict:
        return {}
