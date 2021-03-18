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
3. `config` - configuration files

Example:
```
mkdir data log config
```

## Configuration
Copy the [example.conf](/example.conf) to the `config/` directory. The recommendation is to name it after the
currency (e.g. `BTC-USD` would be `config/btc.conf`)

```
[exchange]
exchange_module = CoinbasePro
key = abc
passphrase = xyz
b64secret = 123

[general]
coin = BTC-USD
sleep_seconds = 60
log_file = log/btc.log
data_file = data/btc.data
pause_file = bot.pause
log_disabled = False

[trader]
trader_module = Simple
max_outstanding_sells = 10
max_buys_per_hour = 10
sell_target = 1.25
buy_barrier = 0.5
buy_percent = 1.0
buy_max = 150.00
buy_min = 35.00
stoploss_enable = no
stoploss_percent = -7.0
stoploss_seconds = 86400
stoploss_strategy = report

[notify]
mail_host = mail.example.com
mail_from = from@example.com
mail_to = to@example.com, other@example.com
notify_only_sold = True

[debug]
debug_response = False
debug_log = log/btc-debug.log
```

## Trading

To start the bot, two commands exist:
1. `botic` - start the bot with specified config
2. `boticp` - wraps `botic` in a loop in case of error (restarts on failure)

Example:
```
boticp config/btc.conf
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
