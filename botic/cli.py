"""CLI entry points for Botic
"""
import os
import sys
import time
from shlex import quote
from .botic import Botic

def usage():
    print('{} <config-file>'.format(sys.argv[0]))
    exit(1)


def main_persist():
    if len(sys.argv) != 2:
        usage()
    try:
        while 1:
            os.system('botic {}'.format(quote(sys.argv[1])))
            time.sleep(60)

    except KeyboardInterrupt:
        print('Exiting...')

def main() -> None:
    if len(sys.argv) != 2:
        usage()
    config_path = sys.argv[1]
    bot = Botic(config_path)
    bot.run()

if __name__ == '__main__':
    main()

