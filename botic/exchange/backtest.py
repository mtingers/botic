"""Backtest exchange module

- Currently handles BTC-USD for the ProductInfo config.
- TODO: Add more

"""
import time
import configparser
import typing as t
import gzip
import datetime
import uuid
import decimal
from pkgutil import get_data
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
        self._orders = {}
        self._last_price = None
        self._maker_fee = Decimal('0.0010')
        self._taker_fee = Decimal('0.0020')
        self._adjusted_time = 0.0

        # TODO: Track volume and adjust fees according to;
        # https://help.coinbase.com/en/pro/trading-and-funding/trading-rules-and-fees/fees
        self._product_info_config = {
            'id':'BTC-USD',
            'display_name':'BTC/USD',
            'base_currency':'BTC',
            'quote_currency':'USD',
            'base_increment':Decimal('0.00000001'),
            'quote_increment':Decimal('0.01000000'),
            'base_min_size':Decimal('0.00100000'),
            'base_max_size':Decimal('280.00000000'),
            'min_market_funds':30,
            'max_market_funds':1000000,
            'status':'online',
            'status_message':'',
            'cancel_only':False,
            'limit_only':False,
            'post_only':False,
            'trading_disabled':False,
            'margin_enabled':False,
        }
        #if self.coin != 'BTC-USD':
        #    raise Exception('Currently only handles BTC-USD')
        gdata = get_data('botic', 'data/historical-btc.csv.gz')
        self._data = gzip.decompress(gdata).decode("utf-8").split('\n')
        self._data_pos = 1
        self._data_buf = []
        self._data_buf_idx = 0
        #"timestamp","low","high","open","close","volume"

    def _prepare_candle(self):
        """
        Convert data frame/candle to a list with filled in points between:
            open -> low/high -> close
        Currently tries something like:
            open -> (open+low)/2 -> (open+low+high)/3 -> high -> (close+low+high)/3 -> close
        """
        try:
            data = self._data[self._data_pos].replace('"', '').split(',')
            tstamp, low, high, x_open, x_close, volume  = [Decimal(i) for i in data]
        except decimal.InvalidOperation:
            self.logit('Backtest has ended. No more data.')
            exit(0)

        if float(tstamp) < self._adjusted_time:
            raise Exception('Time went backwards: tstamp:{} was:{}'.format(
                tstamp, self._adjusted_time))

        self._adjusted_time = float(tstamp)
        # for a check of date
        self._time2datetime()
        #self.adjusted_time = datetime.datetime.fromtimestamp(tstamp)
        self._data_pos += 1
        self._data_buf = []
        open_low = round((x_open+low)/2, 2)
        open_low_high = round((x_open+low+high)/3, 2)
        close_low_high = round((x_close+low+high)/3, 2)
        self._data_buf.append(x_open)
        if not open_low in self._data_buf:
            self._data_buf.append(open_low)
        if not open_low_high in self._data_buf:
            self._data_buf.append(open_low_high)
        if not high in self._data_buf:
            self._data_buf.append(high)
        if not close_low_high in self._data_buf:
            self._data_buf.append(close_low_high)
        if not x_close in self._data_buf:
            self._data_buf.append(x_close)
        self._data_buf_idx = 0

    def authenticate(self):
        return None

    def get_price(self) -> Decimal:
        if not self._data_buf:
            self._prepare_candle()
        price = self._data_buf[self._data_buf_idx]
        self._data_buf_idx += 1
        if self._data_buf_idx >= len(self._data_buf):
            self._prepare_candle()
        self._last_price = Decimal(price)
        self._settle_trades()
        #self._adjusted_time += 1
        return self._last_price

    def _settle_trades(self):
        """Settle trades
        TODO: settle limit buys
        """
        for order_id, val in self._orders.items():
            if val['side'] == 'sell' and val['status'] == 'open':
                price = Decimal(val['price'])
                size = Decimal(val['size'])
                # Sell was filled if latest price is >=
                if price <= self._last_price:
                    val['status'] = 'done'
                    val['done_at'] = self._time2datetime().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                    val['done_reason'] = 'filled'
                    usd_used = size*price
                    fees = round(usd_used * self._maker_fee, 12)
                    executed_value = usd_used - fees
                    self._wallet += executed_value
                    val['executed_value'] = str(executed_value)
                    val['fill_fees'] = str(fees)
                    val['settled'] = True
                    print('exchange-settled: {} last_price:{} -> order:{} / {}'.format(
                        val['id'], self._last_price, price, size))

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
        return self._wallet

    def get_open_sells(self) -> t.List[t.Mapping[str, Decimal]]:
        sells = []
        for _, val in self._orders.items():
            if val['side'] == 'sell' and val['status'] == 'open':
                val['price'] = Decimal(val['price'])
                val['size'] = Decimal(val['size'])
                sells.append(val)
        return sells

    def get_fees(self) -> t.Tuple[Decimal, Decimal, Decimal]:
        return (self._maker_fee, self._taker_fee, Decimal('1'))

    def buy_limit(self, price: Decimal, size: Decimal) -> dict:
        #fixed_price = str(round(Decimal(price), self.usd_decimal_places))
        #fixed_size = str(round(Decimal(size), self.size_decimal_places))
        raise Exception('Not implemented: buy_limit')
        return {}

    def buy_market(self, funds: Decimal) -> dict:
        if funds > self._wallet:
            return {'message':'Insufficient funds'}
        self._wallet = self._wallet - funds
        funds = round(Decimal(funds), self.usd_decimal_places)
        # funds - fees
        fees = round(funds * self._taker_fee, 12)
        executed_value = round(funds - (fees), 12)
        filled_size = round(executed_value/self._last_price, 8)
        uid = str(uuid.uuid4())
        response = {
            'created_at': self._time2datetime().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            'done_at': self._time2datetime().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            'done_reason': 'filled',
            'executed_value': str(executed_value),
            'fill_fees': str(fees),
            'filled_size': str(filled_size),
            'funds': str(executed_value),
            'id': uid,
            'post_only': False,
            'product_id': 'BTC-USD',
            'profile_id': 'xyz',
            'settled': True,
            'side': 'buy',
            'specified_funds': str(funds),
            'status': 'done',
            'type': 'market'
        }
        self.logit('buy_market: funds:{}'.format(funds), custom_datetime=self._time2datetime())
        self._orders[uid] = response
        return response

    def sell_limit(self, price: Decimal, size: Decimal) -> dict:
        fixed_price = str(round(Decimal(price), self.usd_decimal_places))
        fixed_size = str(round(Decimal(size), self.size_decimal_places))
        self.logit('sell_limit: price:{} size:{}'.format(fixed_price, fixed_size),
            custom_datetime=self._time2datetime())
        uid = str(uuid.uuid4())
        response = {
            'created_at': self._time2datetime().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            'executed_value': '0',
            'fill_fees': '0',
            'filled_size': '0',
            'id': uid,
            'post_only': False,
            'price': fixed_price,
            'product_id': 'BTC-USD',
            'settled': False,
            'side': 'sell',
            'size': fixed_size,
            'status': 'open',
            'stp': 'dc',
            'time_in_force': 'GTC',
            'type': 'limit'
        }
        self._orders[uid] = response
        return response

    def sell_market(self, size: Decimal) -> dict:
        fixed_size = str(round(Decimal(size), self.size_decimal_places))
        self.logit('sell_market: size:{}'.format(fixed_size),
            custom_datetime=self._time2datetime())
        uid = str(uuid.uuid4())
        usd_used = Decimal(size) * self._last_price
        fees = round(usd_used * self._taker_fee, 12)
        executed_value = usd_used - fees
        self._wallet += executed_value
        response = {
            'created_at': self._time2datetime().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            'done_at': self._time2datetime().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            'executed_value': str(executed_value),
            'fill_fees': str(fees),
            'filled_size': str(size),
            'id': uid,
            'post_only': False,
            'price': str(self._last_price),
            'product_id': 'BTC-USD',
            'settled': True,
            'side': 'sell',
            'size': fixed_size,
            'status': 'done',
            'stp': 'dc',
            'time_in_force': 'GTC',
            'type': 'market'
        }
        self._orders[uid] = response
        return response

    def cancel(self, order_id: str) -> bool:
        if self._orders[order_id]['status'] == 'open':
            self._orders[order_id]['status'] = 'cancel'
            self._orders[order_id]['settled'] = True
        return self._orders[order_id]

    def get_order(self, order_id: str) -> dict:
        return self._orders[order_id]

    def _time2datetime(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(self._adjusted_time)

    def get_time(self) -> float:
        return self._adjusted_time

    def get_hold_value(self) -> Decimal:
        total = Decimal('0.0')
        price = self._last_price
        for _, info in self._orders.items():
            if info['side'] == 'sell' and info['status'] == 'open':
                amount = Decimal(info['size']) * Decimal(info['price'])
                total += amount
        return total
