"""CLI entry points for Botic
"""
import os
import sys
import time
from shlex import quote
from .botic import Botic

os.environ['TZ'] = 'UTC'
time.tzset()

def usage():
    """Prints the usage information"""
    print('{} <config-file>'.format(sys.argv[0]))
    sys.exit(1)

def main_persist():
    """Run botic in a infinite loop"""
    if len(sys.argv) != 2:
        usage()
    try:
        while 1:
            os.system('botic {}'.format(quote(sys.argv[1])))
            time.sleep(60)

    except KeyboardInterrupt:
        print('Exiting...')

def main() -> None:
    """Run botic"""
    if len(sys.argv) != 2:
        usage()
    config_path = sys.argv[1]
    bot = Botic(config_path)
    try:
        bot.run()
    except KeyboardInterrupt:
        print('exit')

def main_profile() -> None:
    """Run botic with cProfile"""
    import cProfile, pstats, io
    if len(sys.argv) != 2:
        usage()
    config_path = sys.argv[1]
    pr = cProfile.Profile()
    pr.enable()
    bot = Botic(config_path)
    try:
        bot.run()
    except KeyboardInterrupt:
        print('exit')
    s = io.StringIO()
    sortby = 'cumulative'
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats()
    print(s.getvalue())

if __name__ == '__main__':
    main()
