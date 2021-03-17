"""Simple trader"""
import time
from decimal import Decimal
import typing as t
from .base import BaseTrader
from ..util import str2bool, parse_datetime
from ..exchange.exceptions import ExchangeSellLimitError

class Simple(BaseTrader):
    """Simple trader"""
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=attribute-defined-outside-init
    # pylint: disable=no-member
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-function-args
    def __init__(self, config) -> None:
        super().__init__(config)
        self.usd_decimal_places = None
        self.size_decimal_places = None
        self.current_price = None
        self.current_price_target = None
        self.taker_fee = None
        self.maker_fee = None
        self.usd_volume = None
        self.product_info = None
        self.current_price_increase = None
        self.wallet = None
        self.can_buy = False

    def configure(self) -> None:
        self.max_outstanding_sells = int(self.max_outstanding_sells)
        self.max_buys_per_hour = int(self.max_buys_per_hour)
        self.sell_target = Decimal(self.sell_target)
        self.buy_barrier = Decimal(self.buy_barrier)
        self.buy_percent = Decimal(self.buy_percent)
        self.buy_max = Decimal(self.buy_max)
        self.buy_min = Decimal(self.buy_min)
        self.stoploss_enable = str2bool(self.stoploss_enable)
        self.stoploss_percent = Decimal(self.stoploss_percent)
        self.stoploss_seconds = int(self.stoploss_seconds)
        self.stoploss_strategy = str(self.stoploss_strategy)

    def run_trading_algorithm(self) -> None:
        self.product_info = self.exchange.get_product_info()
        self.current_price = self.exchange.get_price()
        self.maker_fee, self.taker_fee, self.usd_volume = self.exchange.get_fees()
        self.size_decimal_places, self.usd_decimal_places = self.exchange.get_precisions()
        self.wallet = self.exchange.get_usd_wallet()
        self._get_current_price_target()
        self.can_buy = self._check_if_can_buy()
        self._maybe_buy_sell()
        self._check_sell_orders()
        self.logit('wallet:{:2f} open-orders:{} price:{} can-buy:{}'.format(
            self.wallet, self._total_open_orders, self.current_price, self.can_buy,
        ))

    @property
    def _total_open_orders(self) -> int:
        total = 0
        for _, order in self.cache.items():
            if not order['completed'] and order['sell_order']:
                total += 1
        return total

    @property
    def _total_sells_in_past_hour(self) -> int:
        current_time = time.time()
        last_hour_time = current_time - (60 * 60)
        total = 0
        for _, order in self.cache.items():
            if order['time'] >= last_hour_time:
                total += 1
        return total

    def _get_current_price_target(self) -> Decimal:
        current_percent_increase = (self.maker_fee + self.taker_fee) + (self.sell_target / 100)
        self.current_price_target = round(
            self.current_price * current_percent_increase + self.current_price,
            self.usd_decimal_places
        )
        self.current_price_increase = self.current_price * current_percent_increase
        return self.current_price_target

    def _check_if_can_buy(self) -> bool:
        """Check orders if a sell price is <= current_price_target.
        If so, this means no buy is allowed until that order is filled or out of range.
        Only allow within the fee range though to keep buy/sells further apart.
        """
        self._get_current_price_target()

        # Check how many buys were placed in past hour and total open
        if self._total_sells_in_past_hour > self.max_buys_per_hour:
            self.logit('WARNING: max_buys_per_hour({}) hit'.format(self.max_buys_per_hour))
            return False

        # Don't count other orders now, only ones being tracked here
        # if len(self.open_sells) >= self.max_outstanding_sells:
        if self._total_open_orders >= self.max_outstanding_sells:
            self.logit('WARNING: max_outstanding_sells hit ({} of {})'.format(
                self._total_open_orders, self.max_outstanding_sells))
            return False
        can = True
        for _, order in self.cache.items():  # self.open_sells:
            if order['completed']:
                continue
            sell_order = order['sell_order']
            if not sell_order:
                continue
            if not 'price' in sell_order:
                continue
            sell_price = Decimal(sell_order['price'])
            fees = self.maker_fee + self.taker_fee
            barrier = self.buy_barrier / Decimal('100.0')
            adjusted_sell_price = round(
                sell_price - ((Decimal(barrier) + fees) * sell_price),
                self.usd_decimal_places
            )
            if adjusted_sell_price <= self.current_price_target:
                can = False
                break
        return can


    def _maybe_buy_sell(self) -> None:
        assert self.wallet is not None, 'Wallet must be set.'
        assert self.current_price is not None, 'Current price must be set.'
        if not self.can_buy:
            return

        # Check if USD wallet has enough available
        if self.wallet < Decimal(self.product_info.min_market_funds):
            self.logit('WARNING: Wallet value too small (<${}): {}'.format(
                self.product_info.min_market_funds, self.wallet))
            return

        # Calculate & check if size is big enough (sometimes its not if wallet is too small)
        buy_amount = round(
            Decimal(self.buy_percent) * Decimal(self.wallet), self.usd_decimal_places
        )
        buy_size = round(Decimal(buy_amount) / self.current_price, self.size_decimal_places)
        if buy_size <= self.product_info.base_min_size:
            self.logit('WARNING: Buy size is too small {} {} < {} wallet:{}.'.format(
                buy_amount, buy_size, self.product_info.base_min_size, self.wallet))
            self.logit('DEBUG: {}'.format(self.product_info.config))
            buy_amount = self.buy_min
            buy_size = round(Decimal(buy_amount) / self.current_price, self.size_decimal_places)
            self.logit('DEFAULT_BUY_SIZE_TO_MIN: {} {}'.format(buy_amount, buy_size))

        # Check if USD wallet has enough available
        if buy_amount < Decimal(self.product_info.min_market_funds):
            self.logit('WARNING: Buy amount too small (<${}): {}'.format(
                self.product_info.min_market_funds, buy_amount))
            buy_amount = self.buy_min
            buy_size = round(Decimal(buy_amount) / self.current_price, self.size_decimal_places)
            self.logit('DEFAULT_BUY_SIZE_TO_MIN: {} {}'.format(buy_amount, buy_size))

        # Make sure buy_amount is within buy_min/max
        if buy_amount < self.buy_min:
            self.logit('WARNING: buy_min hit. Setting to min.')
            buy_amount = self.buy_min
        elif buy_amount > self.buy_max:
            self.logit('WARNING: buy_max hit. Setting to max.')
            buy_amount = self.buy_max

        if Decimal(self.wallet) < Decimal(self.buy_min):
            self.logit('INSUFFICIENT_FUNDS')
            return

        # adjust size to fit with fee
        buy_size = round(
            Decimal(buy_size) - Decimal(buy_size) * Decimal(self.taker_fee),
            self.size_decimal_places
        )
        self.logit('BUY: price:{} amount:{} size:{}'.format(
            self.current_price, buy_amount, buy_size))
        response = self.exchange.buy_market(buy_amount)
        self.logit('BUY-RESPONSE: {}'.format(response))
        if 'message' in response:
            self.logit('WARNING: Failed to buy')
            return
        order_id = response['id']
        errors = 0
        self.last_buy = None
        # Wait until order is completely filled
        if order_id in self.cache:
            self.logit('ERROR: order_id exists in cache. ????: {}'.format(order_id))
        self.cache[order_id] = {
            'first_status': response, 'last_status': None, 'time': time.time(),
            'sell_order': None, 'sell_order_completed': None,
            'completed': False, 'profit_usd': None
        }
        self.write_cache()
        done = False
        status_errors = 0
        buy = {}
        while 1:
            try:
                buy = self.exchange.get_order(order_id)
                self.cache[order_id]['last_status'] = buy
                self.write_cache()
                if 'settled' in buy:
                    if buy['settled']:
                        self.logit('FILLED: size:{} funds:{}'.format(
                            buy['filled_size'], buy['funds']))
                        self.last_buy = buy
                        done = True
                        break
                else:
                    self._handle_failed_order_status(order_id, buy, status_errors)
                    status_errors += 1
                if status_errors > 10:
                    errors += 1
            except Exception as err:
                self.logit('WARNING: get_order() failed:' + str(err))
                errors += 1
                time.sleep(10)
            if errors > 5:
                self.logit('WARNING: Failed to get order. Manual intervention needed.: {}'.format(
                    order_id))
                break
            time.sleep(2)

        # Buy order done, now place sell
        if done:
            msg = 'BUY-FILLED: size:{} funds:{}\n'.format(buy['filled_size'], buy['funds'])
            self.logit(msg)
            try:
                response = self.exchange.sell_limit(
                    self.current_price_target,
                    self.last_buy['filled_size']
                )
                self.logit('SELL-RESPONSE: {}'.format(response))
                msg = '{} SELL-PLACED: size:{} price:{}'.format(
                    msg, self.last_buy['filled_size'], self.current_price_target)
                for i in msg.split('\n'):
                    self.logit(i.strip())
                if not self.notify_only_sold:
                    self.send_email('BUY/SELL', msg=msg)
                self.cache[order_id]['sell_order'] = response
            except ExchangeSellLimitError as err:
                self.logit('ExchangeSellLimitError: {}'.format(err))
                self.cache[order_id]['completed'] = True
                self.cache[order_id]['sell_order'] = None
            self.write_cache()
            self.last_buy = None
        else:
            # buy was placed but could not get order status
            if 'message' in buy:
                msg = 'BUY-PLACED-NOSTATUS: {}\n'.format(buy['message'])
            else:
                msg = 'BUY-PLACED-NOSTATUS: size:{} funds:{}\n'.format(
                    buy['filled_size'], buy['funds'])
            self.logit(msg)
            self.send_email('BUY-ERROR', msg=msg)

    def _handle_failed_order_status(self, order_id: str, status: t.Mapping[str, t.Any]) -> None:
        if 'message' in status:
            self.logit('WARNING: Failed to get order status: {}'.format(status['message']))
            self.logit(
                'WARNING: Order status error may be temporary, due to coinbase issues or exchange '
                'delays. Check: https://status.pro.coinbase.com'
            )
        else:
            self.logit('WARNING: Failed to get order status: {}'.format(order_id))
        time.sleep(10)

    def _run_stoploss(self, buy_order_id: t.AnyStr) -> None:
        """ Cancel sell order, place new market sell to fill immediately
            get response and update cache
        """
        info = self.cache[buy_order_id]
        sell = info['sell_order']
        # cancel
        response = self.exchange.cancel_order(sell['id'])
        self.logit('STOPLOSS: CANCEL-RESPONSE: {}'.format(response))
        time.sleep(5)
        # new order
        response = self.exchange.sell_market(sell['size'])
        self.cache[buy_order_id]['sell_order'] = response
        self.write_cache()
        self.logit('STOPLOSS: SELL-RESPONSE: {}'.format(response))
        order_id = response['id']
        time.sleep(5)
        done = False
        errors = 0
        status_errors = 0
        while 1:
            try:
                status = self.exchange.get_order(order_id)
                self.cache[buy_order_id]['sell_order'] = status
                self.write_cache()
                if 'settled' in status:
                    if status['settled']:
                        self.logit('SELL-FILLED: {}'.format(status))
                        self.cache[buy_order_id]['sell_order_completed'] = status
                        self.write_cache()
                        done = True
                        break
                else:
                    self.handle_failed_order_status(order_id, status)
                    status_errors += 1
                if status_errors > 10:
                    errors += 1
            except Exception as err:
                self.logit('WARNING: get_order() failed:' + str(err))
                errors += 1
                time.sleep(8)
            if errors > 5:
                self.logit('WARNING: Failed to get order. Manual intervention needed.: {}'.format(
                    order_id))
                break
            time.sleep(2)

        if not done:
            self.logit(
                'ERROR: Failed to get_order() for stoploss. This is a TODO item on how to handle'
            )

    def _check_sell_orders(self) -> None:
        """ Check if any sell orders have completed """
        # pylint: disable=too-many-locals
        # pylint: disable=bare-except
        for buy_order_id, info in self.cache.items():
            if self.cache[buy_order_id]['completed']:
                continue
            if not info['sell_order']:
                self.logit('WARNING: No sell_order for buy {}. This should not happen.'.format(
                    buy_order_id))
                if time.time() - info['time'] > 60 * 60 * 2:
                    self.logit('WARNING: Failed to get order status:')
                    self.logit('WARNING: Writing as done/error since it has been > 2 hours.')
                    self.cache[buy_order_id]['completed'] = True
                    self.write_cache()
                continue
            if 'message' in info['sell_order']:
                self.logit(
                    'WARNING: Corrupted sell order, mark as done: {}'.format(info['sell_order']))
                self.cache[buy_order_id]['completed'] = True
                self.cache[buy_order_id]['sell_order'] = None
                self.write_cache()
                self.send_email('SELL-CORRUPTED',
                    msg='WARNING: Corrupted sell order, mark as done: {}'.format(
                        info['sell_order'])
                )
                time.sleep(3600)
                continue
            sell = self.exchange.get_order(info['sell_order']['id'])
            if 'message' in sell:
                self.logit('WARNING: Failed to get sell order status (retrying later): {}'.format(
                    sell['message']))
                if time.time() - info['time'] > 60 * 60 * 2:
                    self.logit('WARNING: Failed to get order status:')
                    self.logit('WARNING: Writing as done/error since it has been > 2 hours.')
                    self.cache[buy_order_id]['completed'] = True
                    self.write_cache()
                continue

            if 'status' in sell and sell['status'] != 'open':
                # calculate profit from buy to sell
                # done, remove buy/sell
                self.cache[buy_order_id]['completed'] = True
                self.cache[buy_order_id]['sell_order_completed'] = sell
                if sell['status'] == 'done':
                    try:
                        first_time = self.cache[buy_order_id]['first_status']['created_at']
                    except:
                        first_time = None
                    sell_value = Decimal(sell['executed_value'])
                    #sell_filled_size = Decimal(sell['filled_size'])
                    #buy_filled_size = Decimal(info['last_status']['filled_size'])
                    buy_value = Decimal(info['last_status']['executed_value'])
                    buy_sell_diff = round(sell_value - buy_value, 2)
                    if first_time:
                        done_at = time.mktime(
                            time.strptime(parse_datetime(first_time), '%Y-%m-%dT%H:%M:%S'))
                    else:
                        done_at = time.mktime(
                            time.strptime(parse_datetime(sell['done_at']), '%Y-%m-%dT%H:%M:%S'))
                    self.cache[buy_order_id]['profit_usd'] = buy_sell_diff
                    msg = 'SOLD: duration:{:.2f} bought:{} sold:{} profit:{}'.format(
                        time.time() - done_at,
                        round(buy_value, 2),
                        round(sell_value, 2),
                        buy_sell_diff
                    )
                    self.logit(msg)
                    self.send_email('SOLD', msg=msg)
                else:
                    self.logit('SOLD-WITH-OTHER-STATUS: {}'.format(sell['status']))
                self.write_cache()
            else:
                # check for stoploss if enabled
                if self.stoploss_enable:
                    created_at = time.mktime(
                        time.strptime(parse_datetime(sell['created_at']), '%Y-%m-%dT%H:%M:%S'))
                    duration = time.time() - created_at
                    bought_price = round(
                        Decimal(info['last_status']['executed_value']) /
                        Decimal(info['last_status']['filled_size']),
                        4
                    )
                    percent_loss = 100 * (self.current_price / bought_price) - Decimal('100.0')
                    stop_seconds = False
                    stop_percent = False
                    if duration >= self.stoploss_seconds:
                        stop_seconds = True
                    if percent_loss <= self.stoploss_percent:
                        stop_percent = True
                    if (stop_seconds or stop_percent) and self.stoploss_strategy == 'report':
                        self.logit('STOPLOSS: percent:{} duration:{}'.format(
                            percent_loss, duration))

                    if self.stoploss_strategy == 'both' and stop_percent and stop_seconds:
                        self.logit('STOPLOSS: stoploss strategy: {} percent:{} duration:{}'.format(
                            self.stoploss_strategy,
                            percent_loss, duration
                        ))
                        self._run_stoploss(buy_order_id)
                    elif self.stoploss_strategy == 'either' and (stop_percent or stop_seconds):
                        self.logit('STOPLOSS: stoploss strategy: {} percent:{} duration:{}'.format(
                            self.stoploss_strategy,
                            percent_loss, duration
                        ))
                        self._run_stoploss(buy_order_id)
