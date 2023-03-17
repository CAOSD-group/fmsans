import os
import sys
import math
import argparse
import time
import multiprocessing
import statistics
import signal

from flamapy.metamodels.fm_metamodel.transformations import UVLReader, UVLWriter

from fm_solver.transformations import FMToFMSans, FMSansWriter, FMSansReader
from fm_solver.utils import utils, fm_utils, logging_utils, timer, sizer
from fm_solver.models.feature_model import FM
from fm_solver.models import fm_sans as fm_sans_utils
from fm_solver.operations import FMConfigurationsNumber
from flamapy.metamodels.pysat_metamodel.operations import SATProductsNumber
from flamapy.metamodels.pysat_metamodel.transformations import FmToPysat
from flamapy.metamodels.bdd_metamodel.transformations import FmToBDD
from flamapy.metamodels.bdd_metamodel.operations import BDDProductsNumber
from fm_solver.operations.fmsans_op import FMSansProductsNumber, FMSansProductsNumberSAT, FMSansProductsNumberBDD


OUTPUTFILE_RESULTS_STATS = 'analysis_script_results.csv'
TIME_ANALYSIS = 'TIME_ANALYSIS'
TIME_OUT = 600  # 10 minutes
TOOLS = ['sat', 'bdd', 'gft', 'fmsans', 'fmsans_sat', 'fmsans_bdd', 'fmsans_gft']
timeout = False


def timeout_handler(signum, frame):
    timeout = True
    print("Time out!")
signal.signal(signal.SIGALRM, timeout_handler)


def get_fm_filepath_models(dir: str) -> list[str]:
    """Get all models from the given directory."""
    models = []
    for root, dirs, files in os.walk(dir):
        for file in files:
            filepath = os.path.join(root, file)
            models.append(filepath)
    return models


def perform_analysis(op, model):
    signal.alarm(TIME_OUT)
    with timer.Timer(name=TIME_ANALYSIS, logger=None):
        result = op().execute(model).get_result()
    signal.alarm(0)
    return result

def main(fm_filepath: str, n_cores: int, runs: int, tool: str) -> None:
    # Get feature model name
    path, filename = os.path.split(fm_filepath)
    filename = '.'.join(filename.split('.')[:-1])

    # Output file for raw data
    output_file = os.path.join(path, f'{filename}_{tool}.csv')

    # Load the feature model
    print(f'Reading feature model... {fm_filepath}')
    if tool.startswith('fmsans'):
        fmsans = FMSansReader(fm_filepath).transform()
        fm = None
        sat_model = None
        bdd_model = None
    else:
        fm = UVLReader(fm_filepath).transform()
        sat_model = FmToPysat(fm).transform()
        bdd_model = FmToBDD(fm).transform()
        fmsans = None

    # Perform analysis
    print(f'Analyzing feature model...')
    stats_results = []
    with open(output_file, 'w', encoding='utf8') as file:
        file.write(f'Run, Time(s){os.linesep}')
        for i in range(1, runs + 1):
            print(f'{i} ', end='', flush=True)
            timeout = False

            op_model_dict = {'sat': (SATProductsNumber, sat_model),
                             'bdd': (BDDProductsNumber, bdd_model),
                             'gft': (FMConfigurationsNumber, fm),
                             'fmsans': (FMSansProductsNumber, fmsans),
                             'fmsans_sat': (FMSansProductsNumberSAT, fmsans),
                             'fmsans_bdd': (FMSansProductsNumberBDD, fmsans),
                             'fmsans_gft': (FMConfigurationsNumber, fmsans.get_feature_model(n_cores) if tool == 'fmsans_gft' else None)}

            op, model = op_model_dict[tool]
            result = perform_analysis(op, model)
            
            if timeout:
                file.write(f'{i}, timeout{os.linesep}')
                return None

            total_time = timer.Timer.timers[TIME_ANALYSIS]
            total_time = round(total_time, 4)
            file.write(f'{i}, {total_time}{os.linesep}')
            stats_results.append(total_time)
    print()

    # Get results
    n_configs = result
    print(f'#Configurations: {n_configs} ({utils.int_to_scientific_notation(n_configs)})')

    # Get stats
    values_median = statistics.median(stats_results)
    values_mean = statistics.mean(stats_results)
    values_stdev = statistics.stdev(stats_results) if len(stats_results) > 1 else 0
    print(f'Time median (analysis): {values_median} s.')
    print(f'Model, Time_median(s), Time_mean(s), Time_stdev(s)')
    print(f'{filename}, {values_median}, {values_mean}, {values_stdev}')

    # Save stats in file
    if not os.path.exists(OUTPUTFILE_RESULTS_STATS):
        with open(OUTPUTFILE_RESULTS_STATS, 'w', encoding='utf8') as file:
            file.write(f'Model, Tool, #Products, Time_median(s), Time_mean(s), Time_stdev(s){os.linesep}')
    with open(OUTPUTFILE_RESULTS_STATS, 'a', encoding='utf8') as file:
        file.write(f'{filename}, {tool}, {utils.int_to_scientific_notation(n_configs)}, {values_median}, {values_mean}, {values_stdev}{os.linesep}')
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyze an FM using the FMSans Solver.')
    input_model = parser.add_mutually_exclusive_group(required=True)
    input_model.add_argument('-d', '--dir', dest='dir', type=str, help='Input directory with the models in the same format (.uvl or .json) to be analyzed.')
    input_model.add_argument('-fm', '--featuremodel', dest='feature_model', type=str, help='Input feature model in UVL (.uvl) or FMSans (.json) format.')
    parser.add_argument('-c', '--cores', dest='n_cores', type=int, required=False, default=1, help='Number of cores (processes) to execute (power of 2) (default = 1).')
    parser.add_argument('-r', '--runs', dest='runs', type=int, required=False, default=1, help='Number of experiments.')
    parser.add_argument('-t', '--tool', dest='tool', type=str, required=False, default='fmsans', help=f'Tool to execute {TOOLS} (default fmsans).')
    args = parser.parse_args()

    if args.n_cores <= 0 or not math.log(args.n_cores, 2).is_integer():
        if args.n_cores == multiprocessing.cpu_count():
            sys.exit(f'The number of cores of this computer is not a power of 2. Please set the -c parameter to a power of 2.')
        else:
            sys.exit(f'The number of cores must be positive and power of 2.')
    if args.feature_model:    
        if not args.feature_model.endswith('.uvl') and not args.feature_model.endswith('.json'):
            sys.exit(f'Error, incorrect file format for {args.feature_model}. It should be a UVL (.uvl) or a FMSans (.json) model.')
        if args.tool not in TOOLS:
            sys.exit(f'Error, incorrect tool to execute. Use one of {TOOLS}.')
        if args.tool.startswith('fmsans') and not args.feature_model.endswith('.json'):
            sys.exit(f'Error, the tool {args.tool} must be executed over a FMSans (.json) model.')
        if not args.tool.startswith('fmsans') and not args.feature_model.endswith('.uvl'):
            sys.exit(f'Error, the tool {args.tool} must be executed over a UVL (.uvl) model.')

        main(args.feature_model, args.n_cores, args.runs, args.tool)

    elif args.dir:
        models = get_fm_filepath_models(args.dir)
        if all(filepath.endswith('.uvl') for filepath in models):
            if args.tool.startswith('fmsans'):
                sys.exit(f'Error, the directory contains UVL models (.uvl) and the tool does not support UVL models.')
        if all(filepath.endswith('.json') for filepath in models):
            if not args.tool.startswith('fmsans'):
                sys.exit(f'Error, the directory contains FMSans models (.json) and the tool does not support FMSans models.')
        else:
            print(f'Warning, the directory contains other files. They will be ignored.')

        for filepath in models:
            if not filepath.endswith('.uvl') and not filepath.endswith('.json'):
                print(f'Skipped file: {filepath}')
            else:
                main(filepath, args.n_cores, args.runs, args.tool)
            

