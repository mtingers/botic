""" Simple helper methods to be used throughout the code
"""
import typing as t

def parse_datetime(value: str) -> str:
 	""" Parse datetime string with optional milliseconds and/or timezone
    	NOTE: Works for Coinbase but needs to be improved.

    Args:
        value (str): String representation of a date and time

    Returns:
        str: A new string without milliseconds and timezone
    """
    return str(value).split('.')[0].split('Z')[0]


def str2bool(value: str) -> bool:
    """ Convert configuration string value to bool, if valid

    Args:
        value (str): String representation of a boolean value (e.g. yes, true, t, 1)

    Returns:
        bool: True or False
    """
    return value.lower() in ("yes", "true", "t", "1")


