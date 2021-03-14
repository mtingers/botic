import os
import importlib
import configparser
from .base import BaseTrader

class Simple(BaseTrader):
    def __init__(self, config) -> None:
        super().__init__(config)
        print('start')

    def configure(self) -> None:
        print('configure_trader_custom')

    def run_trading_algorithm(self) -> None:
        self.logit('run_trading_algorithm')
        self.wallet = self.exchange.get_usd_wallet()
        self.product_info = self.exchange.get_product_info()
        print('wallet:', self.wallet)
