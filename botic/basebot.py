import os
import sys
import time
import typing as t
from random import uniform
import importlib

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
        ('log_file', str, 'simplebot.log'),
        ('cache_file', str, 'simplebot.cache'),
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


class BaseBot:
    """ The base class for exchanges and trading bots
        See CONFIG_DEFAULTS for more information on attributes that are set during _configure().

    Args:
        config_path (str): The path to the configuration file

    Attributes:
        config (configparse.ConfigParser): ConfigParse object from config_path
    """
    def __init__(self, config_path: str, do_print=False) -> None:
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        self._configure(do_print=do_print)

    def _configure(self, do_print=False) -> None:
        """ Calls setattr() on configuration key,val pairs from self.config, or sets defaults from
            CONFIG_DEFAULT. These are setup so they can be accessed like: self.key
            It also sets key,value paris from the [trader] section for the trader module to convert
            to its needs.

        Args:
            do_print (bool): If True, print and log non-auth configuration items
        """
        for section, v in CONF_DEFAULTS.items():
            for key, cast, default in v:
                val = self._getconf(section, key, cast, default)
                # Special conversion to handle percent values and lists
                if key == 'mail_to':
                    val = val.split(',')
                elif key == 'buy_wallet_percent':
                    val = round(val/100.0, 4)
                if do_print and section != 'auth':
                    print('config: [{}][{}] -> {}'.format(section, key, val))
                setattr(self, key, val)
        # Now configure [trader] section, ingest all values as strings (trader module is responsible
        # for conversion)
        for key, val in self.config['trader'].items():
        	setattr(self, key, val)

    def _getconf(self, section: str, key: str, cast: t.Type, default: t.Any) -> t.Any:
        """ Converts configuration values to Python types

        Args:
            section (str): The configuration section of self.config (e.g. 'auth')
            key (str): The section's key to get()
            cast (type): Cast the retrieved value of self.config[section][key]

        Returns:
            any: The value of the configuration section->key
        """
        val = self.config[section].get(key, default)
        if cast == bool:
            val = str2bool(val)
        else:
            val = cast(val)
        return val

    def _log(self, path: t.AnyStr, msg: t.Any) -> None:
        """ TODO: Replace me with Python logging """
        now = datetime.now()
        print('{} {}'.format(now, str(msg).strip()))
        with open(path, 'a') as f:
            f.write('{} {}\n'.format(now, str(msg).strip()))

    def _write_cache(self) -> None:
        """ Write self.cache to disk atomically """
        with open(self.cache_file + '-tmp', "wb") as f:
            pickle.dump(self.cache, f)
            os.fsync(f)
        if os.path.exists(self.cache_file):
            os.rename(self.cache_file, self.cache_file + '-prev')
        os.rename(self.cache_file + '-tmp', self.cache_file)

    def _init_cache(self) -> None:
        """ Verify cache_file name and load existing cache if it exists """
        self.cache = {}
        if not self.cache_file.endswith('.cache'):
            raise Exception('ERROR: Cache filenames must end in .cache')
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "rb") as f:
                self.cache = pickle.load(f)

    def _init_lock(self) -> None:
        """ Initialize and open lockfile.
            Note that this is done to avoid running duplicate configurations at the same time.
        """
        self.lock_file = self.cache_file.replace('.cache', '.lock')
        self.lock = FileLock(self.lock_file, timeout=1)
        try:
            self.lock.acquire()
        except:
            print('ERROR: Failed to acquire lock: {}'.format(self.lock_file))
            print('Is another process already running with this config?')
            exit(1)

    def logit(self, msg: t.Any) -> None:
        """ TODO: Replace me with Python logging """
        if not self.coin in msg:
            msg = '{} {}'.format(self.coin, msg)
        self._log(self.log_file, msg)

