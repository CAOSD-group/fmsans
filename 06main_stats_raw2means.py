import os
import sys
import argparse
import csv
import statistics
from typing import Any


OUTPUTFILE_SUFIXNAME = '_stats'


def read_csvfile(filepath: str):
    data = []
    with open(filepath, 'r', encoding='utf8', newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
        for row in reader:
            data.append(row)
    return data


def main(filepath: str, columns: list[int]):
    # Get path and filename
    path, filename = os.path.split(filepath)
    filename = filename.split('.')[0]
    
    # Read data
    data = read_csvfile(filepath)
    if not data:
        sys.exit(f'Error: invalid file or empty file.')

    result = []
    header = list(data[0].keys())
    for i, fieldname in enumerate(header):
        if i not in columns:
            result.append(data[0][fieldname])
        else:
            values = [float(data[k][fieldname]) for k in range(len(data))]
            values_mean = statistics.mean(values)
            values_stdev = statistics.stdev(values)
            values_median = statistics.median(values)
            result.append(values_mean)
            result.append(values_stdev)
            result.append(values_median)

    # Write output
    output_file = os.path.join(path, f'{filename}{OUTPUTFILE_SUFIXNAME}.csv')
    header.insert(0, 'FM')
    header.insert(1, 'Runs')
    result.insert(0, filename)
    result.insert(1, len(data))
    print(result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate a .csv file with the statistics metrics (mean, stdev, median) from a raw data file with experiments results.')
    parser.add_argument(dest='filepath', type=str, help='File with raw data (.csv).')
    parser.add_argument(dest='columns', nargs='+', type=int, help='Columns numbers with the values to consider (start at 0).')
    args = parser.parse_args()

    if not args.filepath.endswith('.csv'):
        sys.exit(f'Error: .csv file expected.')

    main(args.filepath, args.columns) 
