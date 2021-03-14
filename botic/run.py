"""Simple wrapper for running botic in a loop (in case of errors).
"""
import os
import sys
import time
from shlex import quote


def usage():
    print('{} <config-file>'.format(sys.argv[0]))
    exit(1)


def main():
    if len(sys.argv) != 2:
        usage()
    try:
        while 1:
            os.system('botic {}'.format(quote(sys.argv[1])))
            time.sleep(60)

    except KeyboardInterrupt:
        print('Exiting...')


if __name__ == '__main__':
    main()
