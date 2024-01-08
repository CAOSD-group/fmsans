import os
import argparse
import csv

from fm_solver.transformations import FMSansReader, FMSansWriter
from fm_solver.utils import utils


def main(dirpath: str, prefix_filter: str) -> None:
    # Get all models
    print(f'Getting models from {dirpath}... with filter {prefix_filter}*')
    filespaths = utils.get_filespaths(dirpath)
    filespaths = [s for s in filespaths if utils.get_filename_from_filepath(s).startswith(prefix_filter)]

    if not filespaths:
        print(f'There is not any files to join in the given path: {dirpath}.')
        return None

    # Join models
    join_stats = dict()
    print(f'Joining {len(filespaths)} files...')
    for i, filepath in enumerate(filespaths, 1):
        filename = utils.get_filename_from_filepath(filepath)
        print(f'{i} ', end='', flush=True)

        with open(filepath, newline=os.linesep, encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',', quotechar='"', skipinitialspace=True)
            for row in reader:
                for header in reader.fieldnames:
                    if header == 'Time(s)':
                        join_stats[header] = max(join_stats.get(header, 0.0), float(row[header]))
                    else:
                        join_stats[header] = join_stats.get(header, 0) + int(row[header])
    print()
    print(f'{join_stats}')

    # Serializing the join stats
    print(f'Serializing model...')
    parts_name = filename.split('_')
    filename = parts_name[0] + '_heuristics.csv'
    output_fmsans_filepath = os.path.join(dirpath, f'{filename}')
    with open(output_fmsans_filepath, 'w', newline=os.linesep, encoding='utf-8') as file:
        writer = csv.DictWriter(file, join_stats.keys())
        writer.writeheader()
        writer.writerow(join_stats)
   
    print(f'Heuristics stats saved in {output_fmsans_filepath}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Join all files from heuristics stats (.csv) in a folder.')
    parser.add_argument(dest='dir', type=str, help='Folder with the models.')
    parser.add_argument('-p', dest='prefix', required=False, default='', type=str, help='Prefix to filter the files in the folder to be considered.')
    args = parser.parse_args()

    main(args.dir, args.prefix)
