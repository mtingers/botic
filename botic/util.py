"""Simple helper methods to be used throughout the code"""
import typing as t
from botic.defaults import CONFIG_DEFAULTS

def parse_datetime(value: str) -> str:
    """Parse datetime string with optional milliseconds and/or timezone

    Works for Coinbase but needs to be improved.

    Args:
        value (str): String representation of a date and time

    Returns:
        str: A new string without milliseconds and timezone
    """
    return str(value).split('.')[0].split('Z')[0]


def str2bool(value: str) -> bool:
    """Convert configuration string value to bool, if valid

    Args:
        value (str): String representation of a boolean value (e.g. yes, true, t, 1)

    Returns:
        bool: True or False
    """
    if isinstance(value, bool):
        return value
    return value.lower() in ("yes", "true", "t", "1")

def configure(obj, do_print=False) -> None:
    """Calls setattr() on configuration key,val pairs from obj.config, or sets defaults from
    CONFIG_DEFAULT.

    These are setup so they can be accessed like: obj.key
    It also sets key,value pairs from the [trader] section for the trader module to convert
    to its needs.

    Args:
        do_print (bool): If True, print and log non-auth configuration items
    """
    for section,items in CONFIG_DEFAULTS.items():
        for key, cast, default in items:
            val = getconf(obj.config, section, key, cast, default)
            # Special conversion to handle percent values and lists
            if key == 'mail_to':
                val = val.split(',')
            if not (section == 'exchange' and key in ('key', 'passphrase', 'b64secret')):
                if do_print:
                    print('config: [{}][{}] -> {}'.format(section, key, val))
            setattr(obj, key, val)
    # Now configure [trader] section, ingest all values as strings (trader module is responsible
    # for conversion)
    for key, val in obj.config['trader'].items():
        setattr(obj, key, val)

def getconf(config, section: str, key: str, cast: t.Type, default: t.Any) -> t.Any:
    """Converts configuration values to Python types

    Args:
        section (str): The configuration section of config (e.g. 'auth')
        key (str): The section's key to get()
        cast (type): Cast the retrieved value of config[section][key]

    Returns:
        any: The value of the configuration section->key
    """
    val = config[section].get(key, default)
    if cast == bool:
        val = str2bool(val)
    else:
        val = cast(val)
    return val
