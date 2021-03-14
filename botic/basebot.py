import os
import sys
import time
import typing as t
from random import uniform
from datetime import datetime
from filelock import FileLock
import importlib

class BaseBot:
    """The base class for exchanges and trading bots

    See CONFIG_DEFAULTS for more information on attributes that are set during _configure().

    Args:
        config_path (str): The path to the configuration file

    Attributes:
        config (configparser.ConfigParser): ConfigParse object from config_path
    """
    def __init__(self, config) -> None:
        self.config = config

    def _log(self, path: t.AnyStr, msg: t.Any) -> None:
        """TODO: Replace me with Python logging"""
        now = datetime.now()
        print('{} {}'.format(now, str(msg).strip()))
        with open(path, 'a') as f:
            f.write('{} {}\n'.format(now, str(msg).strip()))

    def _write_cache(self) -> None:
        """Write self.cache to disk atomically"""
        with open(self.cache_file + '-tmp', "wb") as f:
            pickle.dump(self.cache, f)
            os.fsync(f)
        if os.path.exists(self.cache_file):
            os.rename(self.cache_file, self.cache_file + '-prev')
        os.rename(self.cache_file + '-tmp', self.cache_file)

    def _init_cache(self) -> None:
        """Verify cache_file name and load existing cache if it exists"""
        self.cache = {}
        if not self.cache_file.endswith('.cache'):
            raise Exception('ERROR: Cache filenames must end in .cache')
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "rb") as f:
                self.cache = pickle.load(f)

    def _init_lock(self) -> None:
        """Initialize and open lockfile.

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
        """TODO: Replace me with Python logging"""
        if not self.coin in msg:
            msg = '{} {}'.format(self.coin, msg)
        self._log(self.log_file, msg)

