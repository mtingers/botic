"""Template and base class for adding exchange modules"""
import time
from decimal import Decimal
import typing as t
from abc import abstractmethod
import configparser
from ..basebot import BaseBot

class ProductInfo: # pylint: disable=too-few-public-methods
    """Crypto product information class that stores some important information for making buy/sell
    calculations.

    Args:
        config_path (str): The path to the configuration file

    Attributes:
        id (str): Crypto name and fiat currency
        display_name (str): Friendly crypto name
        base_currency (str): crypto name
        quote_currency (str): Fiat currency
        base_increment (Decimal):  Specifies the minimum increment for the base_currency.
        quote_increment (Decimal): Specifies the min order price as well as the price increment.
        base_min_size (Decimal): Min order size
        base_max_size (Decimal): Max order size
        min_market_funds (int): Min funds allowed in a market order
        max_market_funds (int): Max funds allowed in a market order
        status (str): Short description of the exchange status for this coin
        status_message (str): provides any extra information regarding the status if available.
        cancel_only (bool): indicates whether this product only accepts cancel requests for orders
        post_only (bool): indicates whether only maker orders can be placed. No orders will be
            matched when post_only mode is active.
        limit_only (bool): indicates whether this product only accepts limit orders.
        trading_disabled (bool): indicates whether trading is currently restricted on this product,
            this includes whether both new orders and order cancelations are restricted.
    """
    # pylint: disable=too-many-instance-attributes
    def __init__(self, product_info: dict) -> None:
        self.product_info = product_info
        self.config = {
            'id':'',
            'display_name':'',
            'base_currency':'',
            'quote_currency':'',
            'base_increment':Decimal('-1'),
            'quote_increment':Decimal('-1'),
            'base_min_size':Decimal('-1'),
            'base_max_size':Decimal('-1'),
            'min_market_funds':Decimal(-1),
            'max_market_funds':Decimal(-1),
            'status':'',
            'status_message':'',
            'cancel_only':False,
            'limit_only':False,
            'post_only':False,
            'trading_disabled':False,
            'margin_enabled':False,
        }
        self.display_name = ''
        self.base_currency = ''
        self.quote_currency = ''
        self.base_increment = Decimal('-1')
        self.quote_increment = Decimal('-1')
        self.base_min_size = Decimal('-1')
        self.base_max_size = Decimal('-1')
        self.min_market_funds = Decimal(-1)
        self.max_market_funds = Decimal(-1)
        self.status = ''
        self.status_message = ''
        self.cancel_only = False
        self.limit_only = False
        self.post_only = False
        self.trading_disabled = False
        self.margin_enabled = False
        self.digest()

    def	digest(self) -> None:
        """This can be overridden for handling different exchanges
        To do so, map the exchange product info to the self.config values as closely as possible.
        """
        for key,val in self.product_info.items():
            cast = type(self.config[key])
            setattr(self, key, cast(val))

class BaseExchange(BaseBot):
    """Base class of abstractmethods to implement for each exchange. It is important to note that
    each method sets AND returns the same value (e.g. self.price, return self.price).

    Args:
        config_path (str): The path to the configuration file

    Attributes:
        config (configparser.ConfigParser): ConfigParser object from file specified by config_path
    """
    def __init__(self, config: configparser.ConfigParser) -> None:
        super().__init__(config)
        self.client = None

    @abstractmethod
    def authenticate(self):
        """Authenticate/connect to the exchange using credentials from the config

        Sets:
            self.client

        Returns:
            any: Authenticated client object

        Raises:
            ExchangeAuthError
        """

    @abstractmethod
    def get_price(self) -> Decimal:
        """Get latest price of coin from exchange

        Returns:
            Decimal: Decimal value of API response

        Raises:
            PriceError
            ExchangeError

        Notes:
            Example API: https://docs.pro.coinbase.com/#get-product-ticker
        """

    @abstractmethod
    def get_product_info(self) -> ProductInfo:
        """Build ProductInfo object from API response and set price and size precision (how many
        decimal places each can have).

        Returns:
            ProductInfo: Returns the data as a ProductInfo object

        Raises:
            ExchangeProductInfoError

        Notes:
            Example API: https://docs.pro.coinbase.com/#products
        """

    @abstractmethod
    def get_usd_wallet(self) -> Decimal:
        """Get the value of USD wallet

        Returns:
            Decimal: Decimal value of USD wallet

        Raises:
            ExchangeWalletError

        Notes:
            Example API: https://docs.pro.coinbase.com/#accounts

        """

    @abstractmethod
    def get_open_sells(self) -> t.List[t.Mapping[str, Decimal]]:
        """Query exchange for an active list of open sell orders.

        Returns:
            list[dict]: Return a list of orders with values converted to Decimal where applicable

        Raises:
            ExchangeError

        Notes:
            Example API: https://docs.pro.coinbase.com/#orders
        """

    @abstractmethod
    def get_fees(self) -> t.Tuple[Decimal, Decimal]:
        """Get current maker and taker fees and optionally USD volume

        Returns:
            tuple: (maker_fee, taker_fee, usd_volume)

        Raises:
            ExchangeFeesError

        Notes:
            Example API: https://docs.pro.coinbase.com/#fees
        """

    @abstractmethod
    def buy_limit(self, price: Decimal, size: Decimal) -> dict:
        """Place a buy limit order

        Args:
            price (Decimal): Price per crypto
            size: (Decimal): Amount of base currency to buy

        Returns:
            dict: API response on success

        Raises:
            ExchangeBuyLimitError

        Notes:
            Example API: https://docs.pro.coinbase.com/#orders
        """

    @abstractmethod
    def buy_market(self, funds: Decimal) -> dict:
        """Place a buy market order

        Args:
            funds (Decimal): How much of your wallet to use

        Returns:
            dict: API response on success

        Raises:
            ExchangeBuyMarketError

        Notes:
            Example API: https://docs.pro.coinbase.com/#orders
        """

    @abstractmethod
    def sell_limit(self, price: Decimal, size: Decimal) -> dict:
        """Place a sell limit order

        Args:
            price (Decimal): Price per crypto
            size: (Decimal): Amount of base currency to sell

        Returns:
            dict: API response on success

        Raises:
            ExchangeSellError

        Notes:
            Example API: https://docs.pro.coinbase.com/#orders
        """

    @abstractmethod
    def sell_market(self, size: Decimal) -> dict:
        """Place a sell market order

        Args:
            size: (Decimal): Amount of base currency to sell

        Returns:
            dict: API response on success

        Raises:
            ExchangeSellError

        Notes:
            Example API: https://docs.pro.coinbase.com/#orders
        """

    @abstractmethod
    def cancel(self, order_id: str) -> bool:
        """Cancel an order by it's ID

        Args:
            order_id (str): The order ID to cancel

        Returns:
            bool: True of successful, else False

        Raises:
            ExchangeCancelError

        Notes:
            Example API: https://docs.pro.coinbase.com/#cancel-an-order
        """

    @abstractmethod
    def get_order(self, order_id: str) -> dict:
        """Get order by ID

        Args:
            order_id (str): The order ID to get

        Returns:
            dict: API response as a dictionary

        Notes:
            Example API: https://docs.pro.coinbase.com/#get-an-order
        """

    @abstractmethod
    def get_precisions(self) -> tuple:
        """Get usd and size precisions/decimal places

        Returns:
            tuple: (size_decimal_places, usd_decimal_places)
        """

    @abstractmethod
    def get_hold_value(self) -> Decimal:
        """Get value of outstanding sell orders without fees

        Returns:
            Decimal: total value of outstanding sell orders at current price
        """

    def get_time(self) -> float:
        """Optional override: Return the time based off of what the exchange sees.
        This can be useful for running backtesting and emulating timing in the past.

        Returns:
            float: epoch timestamp
        """
        # pylint: disable=no-self-use
        return time.time()
