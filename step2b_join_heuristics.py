import os
import argparse
import csv
import sys
import statistics
from decimal import *
import decimal

from fm_solver.transformations import FMSansReader, FMSansWriter
from fm_solver.transformations.fm_to_fmsans import HEURISTICS
from fm_solver.utils import utils


def get_prefix(filepath: str) -> str:
    return utils.get_filename_from_filepath(filepath).split('_')[0]

def get_heuristic(filepath: str) -> str:
    return utils.get_filename_from_filepath(filepath).split('_')[-1]

def get_process(filepath: str) -> str:
    return utils.get_filename_from_filepath(filepath).split('_')[1]


def join_models(dirpath: str, filespaths: list[str], prefix: str, heuristic: str) -> None:
    # Join models
    print(f'Joining {len(filespaths)} files...')
    all_stats = dict()
    for fi, filepath in enumerate(filespaths, 1):
        filename = utils.get_filename_from_filepath(filepath)
        print(f'{fi} ', end='', flush=True)
        
        with open(filepath, newline=os.linesep, encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',', quotechar='"', skipinitialspace=True)
            for row in reader:
                run = int(row['Run'])
                if all_stats.get(run, None) is None:    
                    all_stats[run] = dict()
                for header in reader.fieldnames:
                    if header == 'Time(s)':
                        all_stats[run][header] = max(all_stats[run].get(header, 0.0), float(row[header]))
                    elif header not in ['Run', 'Heuristic']:
                        all_stats[run][header] = all_stats[run].get(header, 0) + int(row[header])
                    else:
                        all_stats[run][header] = row[header]
        
    print()
    #print(f'{join_stats}')
    #print(f'{all_stats}')

    run = next(iter(all_stats))
    # Serializing the join stats
    print(f'Serializing model...')
    filename = f'{prefix}_heuristics_{heuristic}.csv'
    output_fmsans_filepath = os.path.join(dirpath, f'{filename}')
    with open(output_fmsans_filepath, 'w', newline=os.linesep, encoding='utf-8') as file:
        writer = csv.DictWriter(file, all_stats[run].keys())
        writer.writeheader()
        for r in all_stats:
            
            print(f"Complete {all_stats[r]['Heuristic']} {(decimal.Decimal(all_stats[r]['Avoid'])+decimal.Decimal(all_stats[r]['Analyzed']))/decimal.Decimal(all_stats[r]['TotalTrees'])}")
            print(f"Analyzed Valid {all_stats[r]['ValidAnalyzed']}")
           
            writer.writerow(all_stats[r])

    analyzed = [all_stats[r]['Analyzed'] for r in all_stats.keys()]
    avoids = [all_stats[r]['Avoid'] for r in all_stats.keys()]
    times = [all_stats[r]['Time(s)'] for r in all_stats.keys()]
    totals = [all_stats[r]['TotalTrees'] for r in all_stats.keys()]
    if  statistics.median(avoids) < statistics.median(analyzed):
        ratio = statistics.median(avoids)/statistics.median(analyzed)
    else:
        ratio = utils.int_to_scientific_notation(statistics.median(avoids)//statistics.median(analyzed))

    print(f'''{prefix} ({len(all_stats)} runs): {os.linesep}
         Median analyzed: {statistics.median(analyzed)} ({utils.int_to_scientific_notation(statistics.median(analyzed))}), {os.linesep}
         Mean analyzed: {statistics.mean(analyzed)}, {os.linesep}
         
         Min analyzed: {min(analyzed)}, {os.linesep}
         Max analyzed: {max(analyzed)} ({utils.int_to_scientific_notation(max(analyzed))}), {os.linesep}
         Median times: {statistics.median(times)}, {os.linesep}
         Mean times: {statistics.mean(times)}, {os.linesep}
         
         Min times: {min(times)}, {os.linesep}
         Max times: {max(times)}, {os.linesep}
         
         Totals: {statistics.median(totals)}, {os.linesep}
         Ratio1: Analyzed/Avoid {statistics.median(analyzed)/statistics.median(avoids) if statistics.median(avoids) != 0 else 0}, {os.linesep}
         Ratio2: Avoid/Analyzed {ratio}, {os.linesep}
         Percentage finished: {((statistics.median(avoids) + statistics.median(analyzed)) / statistics.median(totals)) * 100} %, {os.linesep}
         Percentage to be explored: {(1 - ((statistics.median(avoids) + statistics.median(analyzed)) / statistics.median(totals))) * 100} %, {os.linesep}
         ''')
    

    
    # print(f'''{prefix} ({len(all_stats)} runs): {os.linesep}
    #       Median analyzed: {statistics.median(analyzed)}, {os.linesep}
    #       Mean analyzed: {statistics.mean(analyzed)}, {os.linesep}
    #       Median times: {statistics.median(times)}, {os.linesep}
    #       Mean times: {statistics.mean(times)}, {os.linesep}''')
   
    print(f'Heuristics stats saved in {output_fmsans_filepath}')


def main(dirpath: str) -> None:
    # Get all models
    print(f'Getting models from {dirpath}...')
    filespaths = utils.get_filespaths(dirpath)
    if not filespaths:
        print(f'There is not any files to join in the given path: {dirpath}.')
        return None
    
    # Filter models by model's name
    prefixs = {get_prefix(p) for p in filespaths if not "/." in p and get_process(p).isdigit()}
    prefixs_heuristics_dict = dict()
    for prefix in prefixs:
        prefixs_heuristics_dict[prefix] = {get_heuristic(fp) for fp in filespaths if get_prefix(fp) == prefix and get_process(fp).isdigit()}
    
    for prefix in prefixs:
        for heuristic in prefixs_heuristics_dict.get(prefix):
            files = [f for f in filespaths if get_prefix(f) == prefix and get_heuristic(f) == heuristic and get_process(f).isdigit()]
            join_models(dirpath, files, prefix, heuristic)
    #filespaths = [s for s in filespaths if utils.get_filename_from_filepath(s).startswith(prefix_filter)]


if __name__ == '__main__':
    sys.set_int_max_str_digits(5000)
    getcontext().prec = 100
    parser = argparse.ArgumentParser(description='Join all files from heuristics stats (.csv) in a folder.')
    parser.add_argument(dest='dir', type=str, help='Folder with the models.')
    args = parser.parse_args()

    main(args.dir)
