import os
import time
import importlib
import configparser
from random import uniform
from abc import ABCMeta, abstractmethod
from filelock import FileLock
from ..basebot import BaseBot
from ..botic import configure

class BaseTrader(BaseBot):
    """Base class of abstract methods that are to be implented by traders"""
    def __init__(self, config) -> None:
        super().__init__(config)
        """
        self.logit(
            '{} precision:{} usd-precision:{} current-fees:{}/{} min-size:{} max-size:{}'.format(
                self.coin, self.size_decimal_places, self.usd_decimal_places, self.fee_taker,
                self.fee_maker, self.min_size, self.max_size
            ))
        self.logit(
            '{} sleep_seconds:{} sell_at_percent:{} max_sells_outstanding:{} '
            'max_buys_per_hour:{}'.format(
                self.coin, self.sleep_seconds, self.sell_at_percent,
                self.max_sells_outstanding, self.max_buys_per_hour
            ))
        """

    def _init(self):
        self.configure()
        self._init_lock()
        self._init_cache()
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
            raise Exception('Unknown exchange module: {}'.format(self.exchange_module))
        self.exchange = obj(self.config)
        self.exchange.authenticate()
        configure(self.exchange, do_print=False)

    @abstractmethod
    def configure(self) -> None:
        """Method to convert key,value pairs set from the [trader] config section."""
        pass

    @abstractmethod
    def run_trading_algorithm(self) -> None:
        """Run the traders main algorithim. This is responsible for interacting with the exchange
        to fetch data and place buys/sells.
        """
        pass

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


