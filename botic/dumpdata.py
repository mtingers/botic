"""CLI script to dump pickle/data files"""
import sys
import pickle
from pprint import pprint

def main():
    """Read pickle file and pretty print it"""
    with open(sys.argv[1], "rb") as input_fd:
        pprint(pickle.load(input_fd))

if __name__ == '__main__':
    main()
