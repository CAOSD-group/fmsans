import os
import sys
import math
import argparse
import multiprocessing
import statistics
import signal

from flamapy.metamodels.fm_metamodel.models import Feature
from flamapy.metamodels.fm_metamodel.transformations import UVLReader
from flamapy.metamodels.pysat_metamodel.transformations import FmToPysat
from flamapy.metamodels.bdd_metamodel.transformations import FmToBDD

from fm_solver.transformations import FMSansReader
from fm_solver.utils import utils,timer
from fm_solver.operations.fmsans_op import FMSansFullAnalysis, FMSansFullAnalysisSAT, FMSansFullAnalysisBDD
from fm_solver.operations import (
    FMConfigurationsNumber, FMCoreFeatures, FMDeadFeatures,
    FMFullAnalysis, FMFullAnalysisGFT, FMFullAnalysisSAT, FMFullAnalysisBDD
)

OUTPUTFILE_RESULTS_STATS = 'analysis_script_results.csv'
TIME_ANALYSIS = 'TIME_ANALYSIS'
TIME_OUT = 3600  # seconds
TOOLS = ['sat', 'bdd', 'gft', 'fmsans', 'fmsans_sat', 'fmsans_bdd', 'fmsans_gft']


def timeout_handler(signum, frame):
    """Use a system signal to check out time outs."""
    raise Exception(f'Time out! ({TIME_OUT} seconds)')
signal.signal(signal.SIGALRM, timeout_handler)


def get_fm_filepath_models(dir: str) -> list[str]:
    """Get all models from the given directory."""
    models = []
    for root, dirs, files in os.walk(dir):
        for file in files:
            filepath = os.path.join(root, file)
            models.append(filepath)
    return models


def main(fm_filepath: str, n_cores: int, runs: int, tool: str) -> None:
    # Get feature model name
    path, filename = os.path.split(fm_filepath)
    filename = '.'.join(filename.split('.')[:-1])

    # Output file for raw data
    output_file = os.path.join(path, f'{filename}_{tool}.csv')

    # Load the feature model
    print(f'Reading feature model from {fm_filepath}')
    fm = None
    fmsans = None
    sat_model = None
    bdd_model = None
    gft_model = None
    if tool.startswith('fmsans'):
        print(f'  Reading FMSans model (.json)...')
        signal.alarm(TIME_OUT)
        try:
            fmsans = FMSansReader(fm_filepath).transform()
        except Exception as e:
            print(e)
            return None
        signal.alarm(0)
        
        if tool == 'fmsans_gft':
            print(f'    Obtaining GFT model (steps 3 and 6)...')
            signal.alarm(TIME_OUT)
            try:
                gft_model = fmsans.get_feature_model(n_cores)
            except Exception as e:
                print(e)
                return None
            signal.alarm(0)
    else:
        print(f'  Reading FM model (.uvl)...')
        signal.alarm(TIME_OUT)
        try:
            fm = UVLReader(fm_filepath).transform()
        except Exception as e:
                print(e)
                return None
        signal.alarm(0)
        
        if tool == 'sat':
            print(f'    Transforming feature model to SAT...')
            signal.alarm(TIME_OUT)
            try:
                sat_model = FmToPysat(fm).transform()
            except Exception as e:
                print(e)
                return None
            signal.alarm(0)

        elif tool == 'bdd':
            print(f'    Transforming feature model to BDD...')
            signal.alarm(TIME_OUT)
            try:
                bdd_model = FmToBDD(fm).transform()
            except Exception as e:
                print(e)
                return None
            signal.alarm(0)
        
    # Perform analysis
    print(f'Analyzing model...')
    stats_results = []
    with open(output_file, 'w', encoding='utf8') as file:
        file.write(f'Run, Time(s){os.linesep}')
        print(f'Run: ', end='', flush=True)
        for i in range(1, runs + 1):
            print(f'{i} ', end='', flush=True)

            op_model_dict = {'sat': (FMFullAnalysisSAT(), sat_model),
                             'bdd': (FMFullAnalysisBDD(), bdd_model),
                             'gft': (FMFullAnalysis(), fm),
                             'fmsans': (FMSansFullAnalysis(n_cores), fmsans),
                             'fmsans_sat': (FMSansFullAnalysisSAT(n_cores), fmsans),
                             'fmsans_bdd': (FMSansFullAnalysisBDD(n_cores), fmsans),
                             'fmsans_gft': (FMFullAnalysisGFT(), gft_model)}

            op, model = op_model_dict[tool]
            signal.alarm(TIME_OUT)
            try:
                with timer.Timer(name=TIME_ANALYSIS, logger=None):
                    result = op.execute(model).get_result()
            except Exception as e:
                print(e)
                file.write(f'{i}, timeout{os.linesep}')
                return None
            signal.alarm(0)

            total_time = timer.Timer.timers[TIME_ANALYSIS]
            total_time = round(total_time, 4)
            file.write(f'{i}, {total_time}{os.linesep}')
            stats_results.append(total_time)
    print()

    # Get results
    n_configs = result[FMConfigurationsNumber.get_name()]
    n_configs_scientific = {utils.int_to_scientific_notation(n_configs)}
    n_configs_pretty = n_configs_scientific if n_configs > 10e6 else n_configs
    core_features = result[FMCoreFeatures.get_name()]
    #dead_features = result[FMDeadFeatures.get_name()]
    print(f'#Configurations: {n_configs} ({n_configs_scientific})')
    print(f'#Core features: {len(core_features)} {[f.name if isinstance(f, Feature) else f for f in core_features]}')
    #print(f'#Dead features: {len(dead_features)} {[f.name if isinstance(f, Feature) else f for f in dead_features]}')

    # Get stats
    values_median = statistics.median(stats_results)
    values_mean = statistics.mean(stats_results)
    values_stdev = statistics.stdev(stats_results) if len(stats_results) > 1 else 0
    print(f'Time median (analysis): {values_median} s.')
    print(f'Model, Tool, Runs, Cores, #Products, #CoreFeatures, Time_median(s), Time_mean(s), Time_stdev(s)')
    print(f'{filename}, {tool}, {runs}, {n_cores}, {n_configs_pretty}, {len(core_features)}, {values_median}, {values_mean}, {values_stdev}')

    # Save stats in file
    if not os.path.exists(OUTPUTFILE_RESULTS_STATS):
        with open(OUTPUTFILE_RESULTS_STATS, 'w', encoding='utf8') as file:
            file.write(f'Model, Tool, Runs, Cores, #Products, #CoreFeatures, Time_median(s), Time_mean(s), Time_stdev(s){os.linesep}')
    with open(OUTPUTFILE_RESULTS_STATS, 'a', encoding='utf8') as file:
        file.write(f'{filename}, {tool}, {runs}, {n_cores}, {n_configs_pretty}, {len(core_features)}, {values_median}, {values_mean}, {values_stdev}{os.linesep}')
    

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
            

