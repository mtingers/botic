"""Query CoinbasePro public API for historical data and save as CSV file"""
import sys
import time
import datetime
from datetime import timedelta
import cbpro

SIZE = 60

def date2str(dtobj_or_str):
    """Convert date to str"""
    return str(dtobj_or_str).replace(' ', 'T').split('.')[0]+'Z'

def generate_historical_csv(outfile, coin='BTC-USD', days_ago=93):
    """Generate CSV file from coinbase get_product_historic_rates"""
    # pylint: disable=too-many-locals
    public_client = cbpro.PublicClient()
    start_date = datetime.datetime.now() - timedelta(days=days_ago)
    end_date = datetime.datetime.now()
    next_date = start_date + timedelta(minutes=SIZE)
    out_fd = open(outfile, 'w')
    out_fd.write('"timestamp","low","high","open","close","volume"\n')
    while next_date < end_date:
        #print(next_date)
        stats = public_client.get_product_historic_rates(
            coin,
            granularity=SIZE,
            start=date2str(next_date),
            end=date2str(next_date+timedelta(hours=5)))
        if 'message' in stats:
            print(stats['message'])
            sys.exit(1)
        next_date = next_date + timedelta(hours=5)
        # stats are from newest to oldest, so reverse it
        stats.reverse()
        for i in stats:
            (tstamp, low, high, x_open, x_close, x_volume) = i
            #dt = datetime.datetime.fromtimestamp(tstamp)
            #print(dt, x_close)
            out_fd.write('"{}","{}","{}","{}","{}","{}"\n'.format(
                tstamp, low, high, x_open, x_close, x_volume))
        time.sleep(1.1)
