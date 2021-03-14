from .base import BaseExchange, ProductInfo, Decimal
from .exceptions import *
import typing as t
import cbpro

class CoinbasePro(BaseExchange):
    def _api_response_check(self, response, exception_to_raise):
        if 'message' in response:
            raise exception_to_raise(response['message'])

    def authenticate(self) -> cbpro.AuthenticatedClient:
        key = self.config['exchange'].get('key')
        passphrase = self.config['exchange'].get('passphrase')
        b64secret = self.config['exchange'].get('b64secret')
        self.client = cbpro.AuthenticatedClient(key, b64secret, passphrase)
        test = self.client.get_accounts()
        self._api_response_check(test, ExchangeAuthError)
        return self.client

    def get_price(self) -> Decimal:
        ticker = self.client.get_product_ticker(product_id=self.coin)
        self._api_response_check(ticker, ExchangeError)
        self.price = Decimal(ticker['price'])
        return self.price

    def get_product_info(self) -> ProductInfo:
        self.product_info = None
        products = self.client.get_products()
        self._api_response_check(products, ExchangeProductInfoError)
        for p in products:
            if p['id'] == self.coin:
                self.product_info = ProductInfo(p)
                self.product_info.digest()
                break
        assert self.product_info is not None, 'Product info must be set.'
        # Set how many decimal places/precision price and size can have
        self.size_decimal_places = str(self.product_info.base_increment).split('1')[0].count('0')
        self.usd_decimal_places = str(self.product_info.quote_increment).split('1')[0].count('0')
        return self.product_info

    def get_usd_wallet(self) -> Decimal:
        self.wallet = None
        accounts = self.client.get_accounts()
        self._api_response_check(accounts, ExchangeWalletError)
        for account in accounts:
            if account['currency'] == 'USD':
                self.wallet = Decimal(account['available'])
                break
        assert self.wallet is not None, 'USD wallet was not found.'
        return self.wallet


    def get_open_sells(self) -> t.List[t.Mapping[str, Decimal]]:
        orders = self.client.get_orders()
        self._api_response_check(orders, ExchangeGetOrdersError)
        self.open_sells = []
        for order in orders:
            if order['side'] == 'sell' and order['product_id'] == self.coin:
                order['price'] = Decimal(order['price'])
                order['size'] = Decimal(order['size'])
                self.open_sells.append(order)
        return self.open_sells

    def get_fees(self) -> t.Tuple[Decimal, Decimal, Decimal]:
        """ pip cbpro version doesn't have my get_fees() patch, so manually query it """
        fees = self.client._send_message('get', '/fees')
        self._api_response_check(fees, ExchangeFeesError)
        self.maker_fee = Decimal(fees['maker_fee_rate'])
        self.taker_fee = Decimal(fees['taker_fee_rate'])
        self.usd_volume = Decimal(fees['usd_volume'])
        return (self.maker_fee, self.taker_fee, self.usd_volume)

    def buy_limit(self, price: Decimal, size: Decimal) -> dict:
        fixed_price = str(round(Decimal(price), self.usd_decimal_places))
        fixed_size = str(round(Decimal(size), self.size_decimal_places))
        response = self.client.place_limit_order(
            product_id=self.coin,
            side='buy',
            size=fixed_size,
            price=fixed_price,
        )
        self._api_response_check(response, ExchangeBuyLimitError)
        self.buy_response = response
        return self.buy_response

    def buy_market(self, funds: Decimal) -> dict:
        funds = str(round(Decimal(funds), self.usd_decimal_places))
        response = self.client.place_market_order(
            product_id=self.coin,
            side='buy',
            funds=funds,
        )
        self._api_response_check(response, ExchangeBuyMarketError)
        self.buy_response = response
        return self.buy_response

    def sell_limit(self, price: Decimal, size: Decimal) -> dict:
        fixed_price = str(round(Decimal(price), self.usd_decimal_places))
        fixed_size = str(round(Decimal(size), self.size_decimal_places))
        response = self.client.place_limit_order(
            product_id=self.coin,
            side='sell',
            price=fixed_price,
            size=fixed_size,
        )
        self._api_response_check(response, ExchangeSellLimitError)
        self.sell_response = response
        return self.sell_response

    def sell_market(self, size: Decimal) -> dict:
        fixed_size = str(round(Decimal(size), self.size_decimal_places))
        response = self.client.place_market_order(
            product_id=self.coin,
            side='sell',
            size=fixed_size,
        )
        self._api_response_check(response, ExchangeSellMarketError)
        self.sell_response = response

    def cancel(self, order_id: str) -> bool:
        response = self.client.cancel_order(order_id)
        self._api_response_check(response, ExchangeCancelError)
        self.cancel_response = response
        return self.cancel_response

    def get_order(self, order_id: str) -> dict:
        response = self.client.get_order(order_id)
        self._api_response_check(response, ExchangeGetOrderError)
        self.order_response = response
        return self.order_response


