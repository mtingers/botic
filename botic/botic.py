"""Main entry point to load configuration and classes"""
import os
import sys
import time
import typing as t
from random import uniform
import configparser
import importlib
from .util import str2bool

os.environ['TZ'] = 'UTC'
time.tzset()

# Available config options with defaults
CONFIG_DEFAULTS = {
    'exchange': [
        ('exchange_module', str, 'CoinbasePro'),
        ('key', str, ''),
        ('passphrase', str, ''),
        ('b64secret', str, ''),
    ],
    'general': [
        ('coin', str, 'BTC-USD'),
        ('sleep_seconds', int, 60),
        ('log_file', str, 'botic-btc.log'),
        ('cache_file', str, 'botic-btc.cache'),
        ('pause_file', str, 'bot.pause'),
    ],
    'trader': [
        ('trader_module', str, 'Simple'),
        # Optional config for the trader module goes here.
        # The default config reader will get/set all values in the [trader] section as strings.
        # The trader_module is responsible for converting values as needed.
        # Examples:
        #('max_outstanding_sells', int, 10),
        #('max_buys_per_hour', int, 10),
        #('sell_target', Decimal, Decimal('1.25')),
        #('sell_barrier', Decimal, Decimal('0.5')),
        #('buy_percent', Decimal, Decimal('2.0')),
        #('buy_max', Decimal, Decimal('150.00')),
        #('buy_min', Decimal, Decimal('35.00')),
        #('stoploss_enable', bool, False),
        #('stoploss_percent', Decimal, Decimal('-7.0')),
        #('stoploss_seconds', int, 86400),
        #('stoploss_strategy', str, 'report'),
    ],
    'notify': [
        ('notify_only_sold', bool, False),
        ('mail_host', str, ''),
        ('mail_from', str, ''),
        ('mail_to', str, ''),
    ],
    'debug': [
        ('debug_response', bool, False),
        ('debug_log', str, 'simplebot-debug.log'),
    ],
}

class Botic:
    def __init__(self, config_path: str, do_print=False) -> None:
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        self._configure(do_print=do_print)
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
        print('MOD_PATH:', mod_path)
        #mod = importlib.import_module(mod_path)# , package='botic')
        mod = importlib.import_module('botic.trader')# , package='botic')
        obj = getattr(mod, self.trader, None)
        if not obj:
            raise Exception('Unknown trader module: {}'.format(self.trader_module))
        self.trader = obj(config)

    def _configure(self, do_print=False) -> None:
        """Calls setattr() on configuration key,val pairs from self.config, or sets defaults from
        CONFIG_DEFAULT.

        These are setup so they can be accessed like: self.key
        It also sets key,value pairs from the [trader] section for the trader module to convert
        to its needs.

        Args:
            do_print (bool): If True, print and log non-auth configuration items
        """
        for section, v in CONFIG_DEFAULTS.items():
            for key, cast, default in v:
                val = self._getconf(section, key, cast, default)
                # Special conversion to handle percent values and lists
                if key == 'mail_to':
                    val = val.split(',')
                if do_print and (section == 'exchange' and key in ('key', 'passphrase', 'b64secret')):
                    print('config: [{}][{}] -> {}'.format(section, key, val))
                setattr(self, key, val)
        # Now configure [trader] section, ingest all values as strings (trader module is responsible
        # for conversion)
        for key, val in self.config['trader'].items():
        	setattr(self, key, val)

    def _getconf(self, section: str, key: str, cast: t.Type, default: t.Any) -> t.Any:
        """Converts configuration values to Python types

        Args:
            section (str): The configuration section of self.config (e.g. 'auth')
            key (str): The section's key to get()
            cast (type): Cast the retrieved value of self.config[section][key]

        Returns:
            any: The value of the configuration section->key
        """
        val = self.config[section].get(key, default)
        print(section, key, type(val), val)
        if cast == bool:
            val = str2bool(val)
        else:
            val = cast(val)
        return val

    def run(self) -> None:
        """Entry point to start the bot"""
        self.trader.run()


