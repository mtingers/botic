import os
import re
import sys
import glob
import pickle
import time
from collections import OrderedDict
from datetime import datetime
from decimal import Decimal
from operator import getitem
import curses
from curses import endwin
import cbpro

os.environ['TZ'] = 'UTC'
time.tzset()
PRICE_CACHE = {}
PRICE_CACHE_RATE = 93.1331 #update every N seconds
REFRESH = 5.5 #in seconds

def pdiff(old, new):
    try:
        return round(( (Decimal(new) - Decimal(old)) / Decimal(old)) * Decimal('100.0'), 2)
    except:
        return 'unk'

def parse_datetime(d):
    return str(d).split('.')[0].split('Z')[0]

def get_current_price(coin):
    last_update = time.time()
    current_price = Decimal('0.0')
    if not coin in PRICE_CACHE:
        public_client = cbpro.PublicClient()
        ticker = public_client.get_product_ticker(product_id=coin)
        try:
            current_price = Decimal(ticker['price'])
        except Exception as err:
            return None
    else:
        # check cache age
        if time.time() - PRICE_CACHE[coin]['last_update'] > PRICE_CACHE_RATE:
            public_client = cbpro.PublicClient()
            ticker = public_client.get_product_ticker(product_id=coin)
            current_price = Decimal(ticker['price'])
        else:
            last_update = PRICE_CACHE[coin]['last_update']
            current_price  = PRICE_CACHE[coin]['price']
    PRICE_CACHE[coin] = {'price':current_price, 'last_update':last_update}
    return Decimal(current_price)

def sec2time(sec):
    """ TODO: Replace this function as it is buggy """
    if hasattr(sec,'__len__'):
        return [sec2time(s) for s in sec]
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    pattern = r'%2dh %2dm %2ds'
    if h == 0 and m == 0 and d == 0:
        return r'%2ds' % (s)
    if h == 0 and d == 0:
        return r'%2dm %2ds' % (m, s)
    if d == 0:
        #return pattern % (h, m, s)
        return r'%2dh %2dm %2ds'  % (h, m, s)
    return ('%dd' + pattern) % (d, h, m, s)


def avg(l):
    if len(l) < 1:
        return Decimal(0.0)
    return Decimal(sum(l))/len(l)


def get_open_orders(regex_str):
    files = glob.glob(sys.argv[1]+'/*.data')
    stats = {}
    stats_incomplete = {}
    recent = []
    cur_time = time.time()
    open_times = []
    profit_dates = {}
    output = []
    open_orders_title = '{:>15} {:>9} {:>13} {:>13} {:>14} {:>11}'.format(
        'Duration', 'Coin', 'Bought', 'Sell-Price', 'Size', 'Diff%',
    )
    output.append(open_orders_title)
    for f in files:
        data = None
        coin = None
        with open(f, "rb") as fd:
            data = pickle.load(fd)
        if not data:
            continue
        for order_id in data:
            v = data[order_id]
            data[order_id]['created_at'] = v['first_status']['created_at']
        sorted_data = OrderedDict(sorted(data.items(), key = lambda x: getitem(x[1], 'created_at'), reverse=True))
        for order_id, v in sorted_data.items():
            if not v['first_status']:
                continue
            coin = v['first_status']['product_id']
            if regex_str and not re.search(regex_str, coin, re.IGNORECASE):
                continue
            if v['completed'] or not v['sell_order']:
                continue
            sell = v['sell_order']
            created_at = time.mktime(time.strptime(parse_datetime(sell['created_at']), '%Y-%m-%dT%H:%M:%S'))
            duration = cur_time - created_at
            try:
                price = sell['price']
            except Exception as err:
                price = str(err)
            size = sell['size']
            bought_price = round(Decimal(v['last_status']['executed_value']) / Decimal(v['last_status']['filled_size']), 4)
            cur_price = get_current_price(sell['product_id'])
            output.append('{:>15} {:>9} {:>13} {:>13} {:>13} {:>11}'.format(
                sec2time(duration),
                sell['product_id'],
                bought_price, price,
                size,
                pdiff(bought_price, cur_price),
                #round(cur_price - bought_price, 2)
            ))
    return output

def get_stats(regex_str):
    files = glob.glob(sys.argv[1]+'/*.data')
    stats = {}
    stats_incomplete = {}
    recent = []
    cur_time = time.time()
    open_times = []
    profit_dates = {}
    open_percents = []
    output = []
    output_open_orders = []
    output_daily_profits = []
    output_recent = []
    for f in files:
        data = None
        coin = None
        with open(f, "rb") as fd:
            data = pickle.load(fd)
        if not data:
            continue

        for order_id, v in data.items():
            if not v['first_status']:
                continue
            coin = v['first_status']['product_id']
            if regex_str:
                if not re.search(regex_str, coin, re.IGNORECASE):
                    continue
            if not coin in stats:
                stats[coin] = {
                    'epoch_diffs':[], 'profits':[], 'profits_total':Decimal('0.0'),
                    'open_orders':0, 'done_orders':0, 'avg_close_time':0.0, 'error_orders':0,
                }
            first_status = v['first_status']
            epoch = time.mktime(time.strptime(parse_datetime(first_status['created_at']), '%Y-%m-%dT%H:%M:%S'))
            if v['completed'] and 'sell_order_completed' in v and v['sell_order_completed'] and v['profit_usd']:
                # NOTE: Getting some completed orders w/o all the information filled in (done_at)
                # This seems to happen when failing to retreive status in the bot code
                date_only = v['sell_order_completed']['done_at'].split('T')[0]
                if not date_only in profit_dates:
                    profit_dates[date_only] = []
                profit_dates[date_only].append(v['profit_usd'])
                end_epoch = time.mktime(time.strptime(parse_datetime(v['sell_order_completed']['done_at']), '%Y-%m-%dT%H:%M:%S'))
                epoch_diff = end_epoch - epoch
                cur_diff = cur_time - end_epoch
                if cur_diff < (86400/12):
                    recent.append((coin, v))
                profit = v['profit_usd']
                stats[coin]['epoch_diffs'].append(epoch_diff)
                stats[coin]['profits'].append(profit)
                stats[coin]['profits_total'] += profit
                stats[coin]['done_orders'] += 1
            elif v['completed']:
                stats[coin]['error_orders'] += 1
            else:
                cur_price = get_current_price(coin)
                try:
                    cur_perc = (100*(cur_price/Decimal(v['sell_order']['price']))) - Decimal('100.0')
                    open_percents.append(cur_perc)
                except Exception as err:
                    # I think sometimes the state drifts after a cancel
                    # and v['sell'] was removed but v['completed'] is not True yet
                    #print('ERR:', err, v['sell_order'])
                    pass
                start_epoch = time.mktime(time.strptime(parse_datetime(v['first_status']['created_at']), '%Y-%m-%dT%H:%M:%S'))
                open_times.append(cur_time - start_epoch)
                stats[coin]['open_orders'] += 1

    sorted_keys = OrderedDict(sorted(stats.items(), key = lambda x: getitem(x[1], 'profits_total'), reverse=True))
    output.append('{:>8} {:>13} {:>7} {:>7} {:>7} {:>12} {:>19}'.format(
        'Coin',
        'Profits',
        'Open',
        'Done',
        'Error',
        'Avg-Profit',
        'Avg-Time',
    ))
    total_profits = Decimal('0.0')
    total_open_orders = 0
    total_done_orders = 0
    total_error_orders = 0
    agg_epoch = []
    agg_profits = []
    for key,v  in sorted_keys.items():
        coin = key
        if regex_str and not re.search(regex_str, coin, re.IGNORECASE):
            continue
        output.append('{:>8} {:>13} {:>7} {:>7} {:>7} {:>12} {:>19}'.format(
            coin,
            '$'+str(round(sum(v['profits']), 2)),
            v['open_orders'],
            v['done_orders'],
            v['error_orders'],
            '$'+str(round(avg(stats[coin]['profits']), 2)),
            sec2time(round(avg(v['epoch_diffs']), 2)) if v['epoch_diffs'] else 'None',

        ))
        agg_epoch.append(round(avg(v['epoch_diffs']), 2) if v['epoch_diffs'] else Decimal('0.0'))
        agg_profits.append(round(avg(stats[coin]['profits']), 2))
        total_open_orders += v['open_orders']
        total_done_orders += v['done_orders']
        total_error_orders += v['error_orders']
        total_profits += round(sum(v['profits']), 2)
    output.append('{:>8} {:>13} {:>7} {:>7} {:>7} {:>12} {:>19}'.format(
            'all',
            '$'+str(total_profits),
            total_open_orders,
            total_done_orders,
            total_error_orders,
            '$'+str(round(avg(agg_profits), 2)),
            sec2time(round(avg(agg_epoch), 2)),

    ))
    if open_times:
        min_open_time = sec2time(round(min(open_times), 2))
        max_open_time = sec2time(round(max(open_times), 2))
        avg_open_time = sec2time(round(avg(open_times), 2))
    else:
        min_open_time = Decimal('0.0')
        max_open_time = Decimal('0.0')
        avg_open_time = Decimal('0.0')
    output_open_orders.append('{:>16} {:>16} {:>16} {:>16}'.format( 'Open order times', 'Min', 'Max', 'Avg'))
    output_open_orders.append('{:>16} {:>16} {:>16} {:>16}'.format(' ', min_open_time, max_open_time, avg_open_time))
    cur_drift = round(avg(open_percents), 2)
    if cur_drift < 0:
        output_open_orders.append('Avg-drift: {}%'.format(cur_drift))
    else:
        output_open_orders.append('Avg-drift: {}%'.format(cur_drift))

    # Last 7 days with profits
    sorted_dates_val = OrderedDict(sorted(profit_dates.items(), key = lambda x: x[1], reverse=True))
    sorted_dates = sorted(profit_dates.keys(), reverse=True)
    x = []
    y = []
    for key in sorted_dates[:7]:
        if regex_str and not re.search(regex_str, key, re.IGNORECASE):
            continue
        val = profit_dates[key]
        date_total = round(sum(val), 2)
        x.append(key)
        y.append(date_total)
    if y:
        total_profit = []
        max_y = max(y)
        width = 50
        for i in range(len(y)):
            key = x[i]
            yy = y[i]
            nstars = int((yy/max_y) * width)
            output_daily_profits.append('{:>11} {} {}'.format(key, '$'+str(yy), '*'*nstars))
            total_profit.append(yy)
        nstars = int((avg(total_profit)/max_y) * width)
        output_daily_profits.append('{:>11} {} {}^'.format('Daily-Avg ', '$'+str(round(avg(total_profit), 2)), ' '*(nstars-1)))
    if recent:
        output_recent.append('{}'.format( 'Recently completed orders', ))
        output_recent.append('    {:>8} {:>11} {:>17} {:>19}'.format('Coin', 'Profit', 'Duration', 'Completed', ))
        # bubble sort, why not
        for i in range(len(recent)-1):
            for j in range(len(recent)-i-1):
                if recent[j][1]['sell_order_completed']['done_at'] < recent[j+1][1]['sell_order_completed']['done_at']:
                    tmp = recent[j+1]
                    recent[j+1] = recent[j]
                    recent[j] = tmp

        for coin, v in recent:
            if regex_str and not re.search(regex_str, coin, re.IGNORECASE):
                continue
            first_status = v['first_status']
            epoch = time.mktime(time.strptime(parse_datetime(first_status['created_at']), '%Y-%m-%dT%H:%M:%S'))
            end_epoch = time.mktime(time.strptime(parse_datetime(v['sell_order_completed']['done_at']), '%Y-%m-%dT%H:%M:%S'))
            epoch_diff = end_epoch - epoch
            cur_diff = cur_time - end_epoch
            profit = round(v['profit_usd'], 2)
            output_recent.append('    {:>8} {:>11} {:>17} {:>19}'.format(
                coin, '$'+str(profit), sec2time(epoch_diff), str(sec2time(cur_diff))+' ago')
            )
    return (output, output_open_orders, output_daily_profits, output_recent)


def addstr_wrap(stdscr, a1, a2, a3=None):
    try:
        if a3:
            stdscr.addstr(a1, a2, a3)
        else:
            stdscr.addstr(a1, a2)
    except:
        pass

def draw_menu(stdscr):
    k = 0
    cursor_x = 0
    cursor_y = 0
    filter_str_title = 'Filter: '
    filter_str = None
    filter_regex = None
    regex_str = None
    filter_capture = False
    can_draw = False
    last_draw = time.time()
    last_open_orders = time.time()
    last_stats = time.time()
    open_orders = get_open_orders(regex_str)
    mode_str = 'Stats'
    open_orders_title = '{:>15} {:>9} {:>13} {:>13} {:>13} {:>11}'.format(
        'Duration', 'Coin', 'Bought', 'Sell-Price', 'Size', 'Diff%',
    )
    stats = get_stats(regex_str)
    curses.use_default_colors()
    # nonblocking so it can fetch stats on an interval
    stdscr.nodelay(True)
    stdscr.clear()
    stdscr.refresh()
    # 0:black, 1:red, 2:green, 3:yellow, 4:blue, 5:magenta, 6:cyan, and 7:white.
    # init_pair: number,text,background
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(2, curses.COLOR_CYAN, -1)
    curses.init_pair(3, curses.COLOR_RED, -1)
    curses.init_pair(4, curses.COLOR_GREEN, -1)
    curses.init_pair(5, curses.COLOR_YELLOW, -1)
    curses.init_pair(6, curses.COLOR_BLUE, -1)
    curses.init_pair(7, curses.COLOR_MAGENTA, -1)
    curses.init_pair(8, curses.COLOR_BLACK, curses.COLOR_CYAN)

    while 1:
        cur_time = time.time()
        # Initialization
        if cur_time - last_draw > 0.5:
            can_draw = True
            last_draw = cur_time
            stdscr.clear()
        else:
            can_draw = False

        height, width = stdscr.getmaxyx()

        if k == curses.KEY_DOWN:
            cursor_y = cursor_y + 1
        elif k == curses.KEY_UP:
            cursor_y = cursor_y - 1
        elif k == curses.KEY_RIGHT:
            cursor_x = cursor_x + 1
        elif k == curses.KEY_LEFT:
            cursor_x = cursor_x - 1

        cursor_x = max(0, cursor_x)
        cursor_x = min(width-1, cursor_x)

        cursor_y = max(0, cursor_y)
        cursor_y = min(height-1, cursor_y)

        # Declaration of strings
        if mode_str == 'Stats':
            statusbar_str = '{} | [q]uit [f]ilter [o]rders | {}'.format(
                mode_str, parse_datetime(datetime.now()))
        elif mode_str == 'Orders':
            statusbar_str = '{} | [q]uit [f]ilter [s]tats | {}'.format(
                mode_str, parse_datetime(datetime.now()))
        # Capture Filter regex and compile on return press
        # if filter_capture render bottom input bar
        if filter_capture:
            if not filter_str:
                filter_str = filter_str_title
            else:
                if k not in (0, -1):
                    if k == 10:
                        regex_str = filter_str.replace(filter_str_title, '').strip()
                        if not regex_str:
                            filter_regex = None
                        else:
                            try:
                                filter_regex = re.compile(regex_str, flags=re.IGNORECASE)
                            except:
                                # Report error?
                                filter_regex = None
                                error_msg = 'ERROR: Failed to compile filter regex!'
                                stdscr.attron(curses.color_pair(1))
                                stdscr.attron(curses.A_BOLD)
                                addstr_wrap(stdscr, height-1, 0, error_msg)
                                addstr_wrap(stdscr, height-1, len(error_msg), " " * (width - len(error_msg) - 1))
                                stdscr.attroff(curses.color_pair(1))
                                stdscr.attroff(curses.A_BOLD)
                        filter_str = None
                        filter_capture = False
                    elif k == 263 and len(filter_str) > len(filter_str_title):
                        filter_str = filter_str[:-1]
                    elif k not in (263, 10):
                        filter_str += chr(k)
            if filter_capture:
                stdscr.attron(curses.color_pair(1))
                addstr_wrap(stdscr, height-1, 0, filter_str)
                addstr_wrap(stdscr, height-1, len(filter_str), " " * (width - len(filter_str) - 1))
                stdscr.attroff(curses.color_pair(1))

        # Render bottom filter bar if not capturing and set
        if not filter_capture and regex_str:
            stdscr.attron(curses.color_pair(1))
            addstr_wrap(stdscr, height-1, 0, regex_str)
            addstr_wrap(stdscr, height-1, len(regex_str), " " * (len(regex_str)))
            stdscr.attroff(curses.color_pair(1))

        # Render status bar
        stdscr.attron(curses.color_pair(8))
        stdscr.attron(curses.A_BOLD)
        addstr_wrap(stdscr, 0, 0, statusbar_str)
        addstr_wrap(stdscr, 0, len(statusbar_str), " " * (width - len(statusbar_str)))
        stdscr.attroff(curses.color_pair(8))
        stdscr.attroff(curses.A_BOLD)
        #stdscr.hline(1, 0, '-', width)

        # Open orders section
        if mode_str == 'Orders':
            if cur_time - last_open_orders > REFRESH:
                last_open_orders = cur_time
                open_orders = get_open_orders(regex_str)
            stdscr.attron(curses.color_pair(7))
            stdscr.attron(curses.A_BOLD)
            i = 0
            #open_orders = ['1','2','3','4','5','6','7','8','9','10','11']
            for i,s in enumerate(open_orders):
                if i+5 > height:
                    break
                addstr_wrap(stdscr, 2+i, 0, s)
                addstr_wrap(stdscr, 2+i, len(s), " " * (width - len(s)))
            if len(open_orders) > 1:
                ndisplayed = '({}/{} displayed)'.format(i, len(open_orders)-1)
                addstr_wrap(stdscr, 3+i, 0, ndisplayed)
                addstr_wrap(stdscr, 3+i, len(ndisplayed), " " * (width - len(ndisplayed)))
            stdscr.attroff(curses.color_pair(7))
            stdscr.attroff(curses.A_BOLD)

        # Stats section
        if mode_str == 'Stats':
            if cur_time - last_stats > REFRESH:
                last_stats = cur_time
                stats = get_stats(regex_str)
            #stdscr.addstr(1, 0, stats_title)
            #stdscr.addstr(1, len(stats_title), " " * (width - len(stats_title)))
            i = 0
            color_pair_i = 4
            for output in stats:
                stdscr.attron(curses.color_pair(color_pair_i))
                stdscr.attron(curses.A_BOLD)
                for s in output:
                    i += 1
                    if i+4 > height:
                        break
                    addstr_wrap(stdscr, 1+i, 0, s)
                    addstr_wrap(stdscr, 1+i, len(s), " " * (width - len(s)))
                i += 1
                stdscr.attroff(curses.color_pair(color_pair_i))
                stdscr.attroff(curses.A_BOLD)
                color_pair_i += 1
        if can_draw:
            stdscr.refresh()

        k = stdscr.getch()
        if k == -1:
            if not filter_capture:
                time.sleep(0.15)
            else:
                time.sleep(0.05)
        elif k == ord('f'):
            filter_capture = True
        elif not filter_capture and k == ord('o') and mode_str == 'Stats':
            mode_str = 'Orders'
        elif not filter_capture and k == ord('s') and mode_str == 'Orders':
            mode_str = 'Stats'
        elif not filter_capture and k == ord('q'):
            break


def main():
    while 1:
        do_restart = False
        try:
            curses.wrapper(draw_menu)
        except KeyboardInterrupt:
            break
        except Exception as err:
            do_restart = True
            endwin()
            print('An unexpected error: {}'.format(err))
            print('Restarting...')
        if not do_restart:
            break
        time.sleep(3)

if __name__ == "__main__":
    main()
