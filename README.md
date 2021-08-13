# botic
Free, open-source, extendable crypto trading bot.

Botic can integrate with multiple exchanges and use different trading algorithms. The current
state only has a few available, but more will come in the future.

# DISCLAIMER

This software is for educational purposes only. Do not risk money which you are afraid to lose. USE
THE SOFTWARE AT YOUR OWN RISK. THE AUTHORS AND ALL AFFILIATES ASSUME NO RESPONSIBILITY FOR YOUR
TRADING RESULTS.

# Install

It is highly recommended to setup a virtualenv before installing. Example:

```
python3 -m venv venv
. venv/bin/activate
```
## PyPI

```
pip install botic
```

## setup.py

```
python setup.py install
```

# Running

## Directory Setup

In the project's directory, it is recommended to create a few sub-directories:
1. `data` - state files to track orders
2. `log` - log files
3. `config` - configuration files in yaml format

Example:
```
mkdir data log config
```

## Configuration
Copy the [example.yaml](/example.yaml) to the `config/` directory.

```yaml
global:
  exchange:
    module: CoinbasePro
    key: xyz
    passphrase: abc
    b64secret: bar==
  notify:
    mail_host: localhost
    mail_from: user@example.com
    mail_to: user@example2.com
    notify_only_sold: True
  general:
    sleep_seconds: 60
    log_dir: log
    data_dir: data
    pause_file: bot.pause
    log_disabled: False
  debug:
    debug_response: False
    debug_dir: debug

---
btcbot:
  trader:
    pair: BTC-USD
    module: Simple
    max_outstanding_sells: 5
    max_buys_per_hour: 10
    sell_target: 2.0
    buy_barrier: 2.0
    buy_percent: 2.5
    buy_max: 233.00
    buy_min: 60.00
    stoploss_enable: no
    stoploss_percent: -7.0
    stoploss_seconds: 86400
    stoploss_strategy: report

---
zrxbot:
  trader:
    pair: ZRX-USD
    trader_module: Simple
    max_outstanding_sells: 3
    max_buys_per_hour: 10
    sell_target: 3.0
    buy_barrier: 3.0
    buy_percent: 1.5
    buy_max: 233.00
    buy_min: 60.00
    stoploss_enable: no
    stoploss_percent: -7.0
    stoploss_seconds: 86400
    stoploss_strategy: report
```

## Trading

To start the bot, two commands exist:
1. `botic` - start the bot with specified config
2. `boticp` - wraps `botic` in a loop in case of error (restarts on failure)

Example:
```
boticp config/botic.yaml
```

# Top Command

```
botictop
```

![botictop](/docs/top1.png)
![simpletop orders](/docs/top2.png)

# Backtesting
To test out different trader modules/algorithms, there is a drop-in
[backtest exchange](/botic/exchange/backtest.py) that provides historical CoinbasePro BTC-USD data.
To use, set the config to `exchange_module = Backtest`.

It's important to note that re-running a backtest may result in a order ID key error. Remove the
configured data file to fix (e.g. `rm data/btc-backtest.data).


# Dump Command
For debug purposes, the dump command can be used to display the data/data files:
```
boticdump data/example.data
```

# Contributing
See [CONTRIBUTING.md](/CONTRIBUTING.md)

# Adding an Exchange

Exchanges modules are stored in [botic/exchange](/botic/exchange). To add another exchange,
copy the base template class and implement the abstract methods. Example:

```
cp -nv botic/exchange/base.py botic/exchange/EXCHANGE_NAME.py
editor botic/exchange/EXCHANGE_NAME.py
```

NOTE: The template base class will likely change or be clarified more in the next few releases.

# Adding a Trader

Trader modules are stored in [botic/trader](/botic/trader). To add another trader,
copy the base template class and implement the abstract methods. Example:

```
cp -nv botic/trader/base.py botic/trader/TRADER_NAME.py
editor botic/trader/TRADER_NAME.py
```

NOTE: The template base class will likely change or be clarified more in the next few releases.


# Containerize
TODO

# Running from systemd
TODO

# Reloading
TODO: Add HUP signal config reload.

Currently reloading is done by killing the process and manually starting it again.
