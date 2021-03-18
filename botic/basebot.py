"""Base class for handling standard things like data files and logs
"""
import os
import sys
import time
import pickle
import smtplib
import typing as t
from datetime import datetime
from abc import ABCMeta
from filelock import FileLock

os.environ['TZ'] = 'UTC'
time.tzset()

class DataNameError(Exception):
    """Invalid data name"""

class BaseBot(metaclass=ABCMeta):
    """The base class for exchanges and trading bots

    See CONFIG_DEFAULTS for more information on attributes that are set during _configure().

    Args:
        config_path (str): The path to the configuration file

    Attributes:
        config (configparser.ConfigParser): ConfigParse object from config_path
    """
    # pylint: disable=attribute-defined-outside-init
    # pylint: disable=too-few-public-methods
    # pylint: disable=no-self-use
    # pylint: disable=bare-except
    # pylint: disable=no-member
    def __init__(self, config) -> None:
        self.config = config


    def init_data(self) -> None:
        """Verify data_file name and load existing data if it exists"""
        self.data = {}
        if not self.data_file.endswith('.data'):
            raise DataNameError('ERROR: Data filenames must end in .data')
        if os.path.exists(self.data_file):
            with open(self.data_file, "rb") as data_fd:
                self.data = pickle.load(data_fd)

    def init_lock(self) -> None:
        """Initialize and open lockfile.

        Note that this is done to avoid running duplicate configurations at the same time.
        """
        self.lock_file = self.data_file.replace('.data', '.lock')
        self.lock = FileLock(self.lock_file, timeout=1)
        try:
            self.lock.acquire()
        except:
            print('ERROR: Failed to acquire lock: {}'.format(self.lock_file))
            print('Is another process already running with this config?')
            sys.exit(1)

    def write_data(self) -> None:
        """Write self.data to disk atomically"""
        with open(self.data_file + '-tmp', "wb") as data_fd:
            pickle.dump(self.data, data_fd)
            os.fsync(data_fd)
        if os.path.exists(self.data_file):
            os.rename(self.data_file, self.data_file + '-prev')
        os.rename(self.data_file + '-tmp', self.data_file)

    def _log(self, path: t.AnyStr, msg: t.Any, custom_datetime=None) -> None:
        """TODO: Replace me with Python logging"""
        if custom_datetime:
            now = custom_datetime
        else:
            now = datetime.now()
        print('{} {}'.format(now, str(msg).strip()))
        if not self.log_disabled:
            with open(path, 'a') as log_fd:
                log_fd.write('{} {}\n'.format(now, str(msg).strip()))

    def logit(self, msg: t.Any, custom_datetime=None) -> None:
        """TODO: Replace me with Python logging"""
        if not self.coin in msg:
            msg = '{} {}'.format(self.coin, msg)
        self._log(self.log_file, msg, custom_datetime=custom_datetime)

    def send_email(self, subject: str, msg: t.Optional[t.AnyStr] = None) -> None:
        """TODO: Add auth, currently setup to relay locally or relay-by-IP"""
        for email in self.mail_to:
            if not email.strip():
                continue
            headers = "From: %s\r\nTo: %s\r\nSubject: %s %s\r\n\r\n" % (
                self.mail_from, email, self.coin, subject)
            if not msg:
                msg2 = subject
            else:
                msg2 = msg
            msg2 = headers + msg2
            server = smtplib.SMTP(self.mail_host)
            server.sendmail(self.mail_from, email, msg2)
            server.quit()
            time.sleep(0.1)
