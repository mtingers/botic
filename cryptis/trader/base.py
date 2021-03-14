import os
import importlib
import configparser
from .base import BaseBot

class BaseTrader(BaseBot):
    """ Base class of abstract methods that are to be implented by traders """
    def __init__(self, config_path: str) -> None:
        super().__init__(config_path, do_print=True)
        self._init_lock()
        self._init_cache()
        self._load_exchange()
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

    def _load_exchange(self) -> None:
        """ Load the exchange module specified in the config.
            Exchange config must follow this format for auto-import:
                config:
                    [exchange]
                    exchange_module = CoinbasePro
                code:
                    exchange/coinbasepro.py -> class CoinbasePro(ExchangeBase): ...
        """
        mod = importlib.import_module('exchange.{}'.format(self.exchange.lower()))
        obj = getattr(mod, self.exchange, None)
        if not obj:
            raise Exception('Unknown Exchange: {}'.format(self.exchange))
        self.exchange = obj(config)


    @abstractmethod
    def configure(self) -> None:
        """ Method to convert key,value pairs set from the [trader] config section.
        """
        pass

    @abstractmethod
    def run_trader(self) -> None:
        pass

    def assert_required(self) -> None:
        """ Assert required values are set. If not, then it is likely a programming error.
        """
        assert self.wallet is not None, 'Wallet must be set.'
        assert self.current_price is not None, 'Current price must be set.'

    def run(self): -> None:
        # Throttle startups randomly
        time.sleep(uniform(1, 5))
        while 1:
            if os.path.exists(self.pause_file):
                self.logit('PAUSE')
                time.sleep(30)
                continue
            self.run_trader()
            self.assert_required()
            self.logit('price:{} fees:{}/{} wallet:{} open-sells:{} target:{} can-buy:{}'.format(
                self.current_price,
                self.fee_taker,
                self.fee_maker,
                self.wallet,
                self.total_open_orders,
                self.current_price_target,
                self.can_buy,
            ))
            time.sleep(self.sleep_seconds)


