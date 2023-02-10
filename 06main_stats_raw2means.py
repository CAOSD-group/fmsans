import os
import sys
import argparse
import csv
import statistics
from typing import Any


OUTPUTFILE_SUFIXNAME = '_stats'


def read_csvfile(filepath: str):
    with open(filepath, 'r', encoding='utf8', newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
        print(type(reader))
    return reader


def main(filepath: str):
    path, filename = os.path.split(filepath)
    filename = filename.split('.')[0]
    
    #data = read_csvfile(filepath)
    #print(data)

    output_file = os.path.join(path, f'{filename}{OUTPUTFILE_SUFIXNAME}.csv')
    print(output_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate a .csv file with the statistics metrics (mean, stdev, median) from a raw data file with experiments results.')
    parser.add_argument(dest='filepath', type=str, help='File with raw data (.csv).')
    parser.add_argument(dest='columns', nargs='+', type=int, help='Columns numbers with the values to consider (start at 0).')
    args = parser.parse_args()

    if not args.filepath.endswith('.csv'):
        sys.exit(f'Error: .csv file expected.')

    main(args.filepath) 
