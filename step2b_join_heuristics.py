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
    print(f'Joining {len(filespaths)} files...')
    all_stats = dict()
    for fi, filepath in enumerate(filespaths, 1):
        filename = utils.get_filename_from_filepath(filepath)
        print(f'{fi} ', end='', flush=True)
        
        with open(filepath, newline=os.linesep, encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',', quotechar='"', skipinitialspace=True)
            for i, row in enumerate(reader):
                join_stats = dict()
                if all_stats.get(i, None) is None:    
                    all_stats[i] = join_stats
                for header in reader.fieldnames:
                    if header == 'Time(s)':
                        all_stats[i][header] = max(all_stats[i].get(header, 0.0), float(row[header]))
                    else:
                        all_stats[i][header] = all_stats[i].get(header, 0) + int(row[header])
        
    print()
    #print(f'{join_stats}')
    print(f'{all_stats}')

    # Serializing the join stats
    print(f'Serializing model...')
    parts_name = filename.split('_')
    filename = parts_name[0] + '_heuristics.csv'
    output_fmsans_filepath = os.path.join(dirpath, f'{filename}')
    with open(output_fmsans_filepath, 'w', newline=os.linesep, encoding='utf-8') as file:
        writer = csv.DictWriter(file, all_stats[0].keys())
        writer.writeheader()
        for r in all_stats:
            print(all_stats[r])
            writer.writerow(all_stats[r])
   
    print(f'Heuristics stats saved in {output_fmsans_filepath}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Join all files from heuristics stats (.csv) in a folder.')
    parser.add_argument(dest='dir', type=str, help='Folder with the models.')
    parser.add_argument('-p', dest='prefix', required=False, default='', type=str, help='Prefix to filter the files in the folder to be considered.')
    args = parser.parse_args()

    main(args.dir, args.prefix)
