import os
import importlib
import configparser
from .base import BaseBot

class Simple(BaseBot):
    def __init__(self, config) -> None:
        super().__init__(config)
        print('start')

    def configure(self) -> None:
        print('configure_trader_custom')

    def run_trader(self) -> None:
        print('run_trader')
