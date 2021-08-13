"""Main entry point to load configuration and classes"""
import os
import time
import importlib
from random import uniform
import yaml
from .util import configure

os.environ['TZ'] = 'UTC'
time.tzset()

class UnknownTraderModuleError(Exception):
    """Unknown trader module"""

class DuplicateConfigurationError(Exception):
    """Duplicate config name"""

class BoticProcess:
    """Botic base class to setup and start the trader"""
    # pylint: disable=too-few-public-methods
    # pylint: disable=no-member
    def __init__(self, process_name: str, config: dict, do_print=True) -> None:
        self.process_name = process_name
        self.config = config
        configure(process_name, self, do_print=do_print)
        self._setup_trader()

    def _setup_trader(self) -> None:
        """Load the trader module specified in the config.

        Exchange config must follow this format for auto-import:
            config:
                [trader]
                trader_module = Simple
            code:
                trader/simple.py -> class Simple(BaseTrader): ...
        """
        mod_path = 'botic.trader.{}'.format(self.trader_module.lower())
        mod = importlib.import_module(mod_path) #, package='botic')
        obj = getattr(mod, self.trader_module, None)
        if not obj:
            raise UnknownTraderModuleError('Unknown trader module: {}'.format(self.trader_module))
        self.trader = obj(self.config)
        # Write config vars to trader object
        configure(self.process_name, self.trader, do_print=False)

class Botic:
    """Wrapper to Botic class to configure each global + yaml section"""
    # pylint: disable=too-few-public-methods
    # pylint: disable=no-member
    def __init__(self, config_path: str, do_print=True) -> None:
        self.processes = {}
        with open(config_path) as config_stream:
            self.config = list(yaml.safe_load_all(config_stream))
        self._setup_processes()

    def _setup_processes(self) -> None:
        global_config = None
        for item in self.config:
            if 'global' in item.keys():
                global_config = item['global']
                break
        if not global_config:
            print('WARNING: No global config section found')
        for section in self.config:
            for name, config in section.items():
                if name == 'global':
                    continue
                print('Create process:', name)
                if global_config:
                    for k,v in global_config.items():
                        if not k in config:
                            print('Insert global config:', k)
                            config[k] = v
                proc = BoticProcess(name, config)
                if name in self.processes:
                    raise DuplicateConfigurationError('Duplicate config name: {}'.format(name))
                self.processes[name] = proc

    def run(self) -> None:
        """Entry point to start the bots"""
        run_timer = {}
        for name, obj in self.processes.items():
            run_timer[name] = time.time() - (obj.sleep_seconds+1)
            obj.trader._init()
            time.sleep(uniform(0.2, 1.5))
        while 1:
            min_time_distance = 200.00
            for name, obj in self.processes.items():
                time_diff = time.time() - run_timer[name]
                sleep_diff = obj.sleep_seconds - time_diff
                if sleep_diff < min_time_distance:
                    min_time_distance = sleep_diff
                if os.path.exists(obj.pause_file):
                    obj.trader.logit('PAUSE')
                    run_timer[name] = time.time()
                    continue
                if time_diff >= obj.sleep_seconds:
                    obj.trader.logit('Running: {}'.format(name))
                    obj.trader.run_trading_algorithm()
                    run_timer[name] = time.time()
                    time.sleep(1)
                else:
                    obj.trader.logit('pausing({} < {}): {}'.format(
                        time.time() - run_timer[name], obj.sleep_seconds, name))
                time.sleep(0.1)
            min_time_distance = round(min_time_distance/1.5, 2)
            if min_time_distance < 0:
                min_time_distance = 1

            time.sleep(min_time_distance)

