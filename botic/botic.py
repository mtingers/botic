"""Main entry point to load configuration and classes"""
import os
import time
import configparser
import importlib
from .util import configure

os.environ['TZ'] = 'UTC'
time.tzset()

class UnknownTraderModuleError(Exception):
    """Unknown trader module"""

class Botic:
    """Botic base class to setup and start the trader"""
    # pylint: disable=too-few-public-methods
    # pylint: disable=no-member
    def __init__(self, config_path: str, do_print=True) -> None:
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        configure(self, do_print=do_print)
        self._setup_trader()

    def _setup_trader(self) -> None:
        """Load the trader module specified in the config.

        Exchange config must follow this format for auto-import:
            config:
                [trader]
                trader_module = Simple
            code:
                trader/simple.py -> class Simple(BaseTrader): ...
        """
        mod_path = 'botic.trader.{}'.format(self.trader_module.lower())
        mod = importlib.import_module(mod_path) #, package='botic')
        obj = getattr(mod, self.trader_module, None)
        if not obj:
            raise UnknownTraderModuleError('Unknown trader module: {}'.format(self.trader_module))
        self.trader = obj(self.config)
        # Write config vars to trader object
        configure(self.trader, do_print=False)

    def run(self) -> None:
        """Entry point to start the bot"""
        self.trader.run()
