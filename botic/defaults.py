"""A place to add configuration defaults"""

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
        ('sleep_seconds', float, 60),
        ('log_file', str, 'botic-btc.log'),
        ('data_file', str, 'botic-btc.data'),
        ('pause_file', str, 'bot.pause'),
        ('log_disabled', bool, False),
    ],
    'trader': [
        ('trader_module', str, 'Simple'),
        # Optional config for the trader module goes here.
        # All trader modules can have their own custom names for these key/value pairs.
        # The default config reader will get/set all values in the [trader] section as strings.
        # The trader_module is responsible for converting values as needed.
        # Examples:
        #('max_outstanding_sells', int, 10),
        #('max_buys_per_hour', int, 10),
        #('sell_target', Decimal, Decimal('1.25')),
        #('buy_barrier', Decimal, Decimal('0.5')),
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
        ('debug_log', str, 'botic-debug.log'),
    ],
}
