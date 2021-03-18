"""CoinbasePro exchange module"""
import time
import configparser
import typing as t
import cbpro
from .exceptions import ExchangeError, ExchangeGetOrdersError, ExchangeAuthError
from .exceptions import ExchangeBuyLimitError, ExchangeBuyMarketError, ExchangeSellLimitError
from .exceptions import ExchangeSellMarketError, ExchangeProductInfoError, ExchangeCancelError
from .exceptions import ExchangeFeesError, ExchangeWalletError
from .base import BaseExchange, ProductInfo, Decimal

def _api_response_check(response, exception_to_raise):
    """Raise exception_to_raise if API response contains 'message'. If response['message']
    exists, this is _always_ (I think) and error scenario with CoinbasePro
    """
    if 'message' in response:
        raise exception_to_raise(response['message'])

class CoinbasePro(BaseExchange):
    """CoinbasePro exchange"""
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=no-member
    def __init__(self, config: configparser.ConfigParser) -> None:
        self.usd_decimal_places = 2
        self.size_decimal_places = 8
        super().__init__(config)
        self._last_call = time.time()

    def _rate_limit(self):
        cur_time = time.time()
        if cur_time - self._last_call < 1:
            time.sleep(0.5)
        self._last_call = cur_time

    def _wrap_client(self, method: str, *args, **kwargs):
        self._rate_limit()
        meth = getattr(self.client, method, None)
        for error in range(12):
            try:
                return meth(*args, **kwargs)
            except Exception as err:
                print('WARNING: exchange client error retry: {}'.format(err))
                errors += 1
                if error > 9:
                    raise
                time.sleep(10)

    def authenticate(self) -> cbpro.AuthenticatedClient:
        key = self.config['exchange'].get('key')
        passphrase = self.config['exchange'].get('passphrase')
        b64secret = self.config['exchange'].get('b64secret')
        self.client = cbpro.AuthenticatedClient(key, b64secret, passphrase)
        test = self.client.get_accounts()
        _api_response_check(test, ExchangeAuthError)
        return self.client

    def get_price(self) -> Decimal:
        ticker = self._wrap_client('get_product_ticker', product_id=self.coin)
        _api_response_check(ticker, ExchangeError)
        price = Decimal(ticker['price'])
        return price

    def get_precisions(self) -> ProductInfo:
        product_info = self.get_product_info()
        assert product_info is not None, 'Product info must be set.'
        # Set how many decimal places/precision price and size can have
        base_increment = '%.12f' % (product_info.base_increment)
        quote_increment = '%.12f' % (product_info.quote_increment)
        self.size_decimal_places = base_increment.split('1')[0].count('0')
        self.usd_decimal_places = quote_increment.split('1')[0].count('0')
        return (self.size_decimal_places, self.usd_decimal_places)

    def get_product_info(self) -> ProductInfo:
        product_info = None
        products = self._wrap_client('get_products')
        _api_response_check(products, ExchangeProductInfoError)
        for product in products:
            if product['id'] == self.coin:
                product_info = ProductInfo(product)
                product_info.digest()
                break
        assert product_info is not None, 'Product info must be set.'
        return product_info

    def get_usd_wallet(self) -> Decimal:
        accounts = self._wrap_client('get_accounts')
        _api_response_check(accounts, ExchangeWalletError)
        for account in accounts:
            if account['currency'] == 'USD':
                wallet = Decimal(account['available'])
                break
        assert wallet is not None, 'USD wallet was not found.'
        return wallet

    def get_open_sells(self) -> t.List[t.Mapping[str, Decimal]]:
        orders = self._wrap_client('get_orders')
        _api_response_check(orders, ExchangeGetOrdersError)
        open_sells = []
        for order in orders:
            if order['side'] == 'sell' and order['product_id'] == self.coin:
                order['price'] = Decimal(order['price'])
                order['size'] = Decimal(order['size'])
                open_sells.append(order)
        return open_sells

    def get_fees(self) -> t.Tuple[Decimal, Decimal, Decimal]:
        """pypi cbpro version doesn't have my get_fees() patch, so manually query it"""
        # pylint: disable=protected-access
        #fees = self.client._send_message('get', '/fees')
        fees = self._wrap_client('_send_message', 'get', '/fees')
        _api_response_check(fees, ExchangeFeesError)
        maker_fee = Decimal(fees['maker_fee_rate'])
        taker_fee = Decimal(fees['taker_fee_rate'])
        usd_volume = Decimal(fees['usd_volume'])
        return (maker_fee, taker_fee, usd_volume)

    def buy_limit(self, price: Decimal, size: Decimal) -> dict:
        fixed_price = str(round(Decimal(price), self.usd_decimal_places))
        fixed_size = str(round(Decimal(size), self.size_decimal_places))
        response = self._wrap_client('place_limit_order',
            product_id=self.coin,
            side='buy',
            size=fixed_size,
            price=fixed_price,
        )
        _api_response_check(response, ExchangeBuyLimitError)
        return response

    def buy_market(self, funds: Decimal) -> dict:
        funds = str(round(Decimal(funds), self.usd_decimal_places))
        self.logit('buy_market: funds:{}'.format(funds))
        response = self._wrap_client('place_market_order',
            product_id=self.coin,
            side='buy',
            funds=funds,
        )
        _api_response_check(response, ExchangeBuyMarketError)
        return response

    def sell_limit(self, price: Decimal, size: Decimal) -> dict:
        fixed_price = str(round(Decimal(price), self.usd_decimal_places))
        fixed_size = str(round(Decimal(size), self.size_decimal_places))
        self.logit('sell_limit: price:{} size:{}'.format(fixed_price, fixed_size))
        response = self._wrap_client('place_limit_order',
            product_id=self.coin,
            side='sell',
            price=fixed_price,
            size=fixed_size,
        )
        _api_response_check(response, ExchangeSellLimitError)
        return response

    def sell_market(self, size: Decimal) -> dict:
        fixed_size = str(round(Decimal(size), self.size_decimal_places))
        self.logit('sell_market: size:{}'.format(fixed_size))
        response = self._wrap_client('place_market_order',
            product_id=self.coin,
            side='sell',
            size=fixed_size,
        )
        _api_response_check(response, ExchangeSellMarketError)
        return response

    def cancel(self, order_id: str) -> bool:
        response = self._wrap_client('cancel_order', order_id)
        _api_response_check(response, ExchangeCancelError)
        return response

    def get_order(self, order_id: str) -> dict:
        response = self._wrap_client('get_order', order_id)
        _api_response_check(response, ExchangeGetOrdersError)
        return response

    def get_hold_value(self) -> Decimal:
        return Decimal(-1)
