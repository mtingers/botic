"""Exchange specific errors"""

class PriceError(Exception):
    """Could not convert price string to Decimal"""

class ExchangeError(Exception):
    """Generic exchange error"""

class ExchangeGetOrdersError(Exception):
    """Exchange get orders failed"""

class ExchangeAuthError(Exception):
    """Exchange authentication failed"""

class ExchangeBuyLimitError(Exception):
    """Exchange limit buy failed"""

class ExchangeBuyMarketError(Exception):
    """Exchange market buy failed"""

class ExchangeSellLimitError(Exception):
    """Exchange limit sell failed"""

class ExchangeSellMarketError(Exception):
    """Exchange market sell failed"""

class ExchangeProductInfoError(Exception):
    """Exchange product info failed"""

class ExchangeCancelError(Exception):
    """Exchange cancel order failed"""

class ExchangeFeesError(Exception):
    """Exchange get fees failed"""

class ExchangeWalletError(Exception):
    """Exchange get accounts failed"""
