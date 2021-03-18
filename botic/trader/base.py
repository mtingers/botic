"""Base class of abstract methods that are to be implented by traders"""
import os
import time
import importlib
from random import uniform
from abc import abstractmethod
from ..basebot import BaseBot
from ..botic import configure

class UnknownExchangeModuleError(Exception):
    """Unknown trader module"""

class BaseTrader(BaseBot):
    """Base class of abstract methods that are to be implented by traders"""
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=no-member
    # pylint: disable=attribute-defined-outside-init
    def _init(self) -> None:
        """Initialize configuration, lock, data and load exchange"""
        self.configure()
        self.init_lock()
        self.init_data()
        self._load_exchange()

    def _load_exchange(self) -> None:
        """Load the exchange module specified in the config.

        Exchange config must follow this format for auto-import:
            config:
                [exchange]
                exchange_module = CoinbasePro
            code:
                exchange/coinbasepro.py -> class CoinbasePro(ExchangeBase): ...
        """
        mod_path = 'botic.exchange.{}'.format(self.exchange_module.lower())
        mod = importlib.import_module(mod_path)
        obj = getattr(mod, self.exchange_module, None)
        if not obj:
            raise UnknownExchangeModuleError('Unknown exchange module: {}'.format(
                self.exchange_module))
        self.exchange = obj(self.config)
        self.exchange.authenticate()
        configure(self.exchange, do_print=False)

    @abstractmethod
    def configure(self) -> None:
        """Method to convert key,value pairs set from the [trader] config section."""

    @abstractmethod
    def run_trading_algorithm(self) -> None:
        """Run the traders main algorithim. This is responsible for interacting with the exchange
        to fetch data and place buys/sells.
        """

    def run(self) -> None:
        """Main program loop"""
        self._init()
        # Throttle startups randomly
        time.sleep(uniform(1, 5))
        while 1:
            if os.path.exists(self.pause_file):
                self.logit('PAUSE')
                time.sleep(30)
                continue
            self.run_trading_algorithm()
            time.sleep(self.sleep_seconds)
