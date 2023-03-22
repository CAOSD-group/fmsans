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
from fm_solver.operations import FMConfigurationsNumber, FMConfigurations, FMCoreFeatures, FMFullAnalysis, FMFullAnalysisBDD, FMFullAnalysisSAT
from flamapy.metamodels.pysat_metamodel.operations import SATCoreFeatures
from flamapy.metamodels.pysat_metamodel.transformations import FmToPysat
from flamapy.metamodels.bdd_metamodel.transformations import FmToBDD


TIME_ANALYSIS = 'TIME_ANALYSIS'
TIME_OUT = 600  # 10 minutes


def timeout_handler(signum, frame):
    print("Time out!")
    raise Exception("Time out.")
signal.signal(signal.SIGALRM, timeout_handler)


def main(fm_filepath: str, n_cores: int, runs: int) -> None:
    # Get feature model name
    path, filename = os.path.split(fm_filepath)
    filename = '.'.join(filename.split('.')[:-1])

    # Load the feature model (FMSans)
    print(f'Reading FMSans model... {fm_filepath}')
    fm = UVLReader(fm_filepath).transform()
    bdd_model = FmToBDD(fm).transform()

    # Perform full analysis of FMSans
    print(f'Analyzing FM...')
    stats_results = []
    print(f'Run, Time(s)')
    for i in range(1, runs + 1):
        signal.alarm(TIME_OUT)
        with timer.Timer(name=TIME_ANALYSIS, logger=None):
            result = FMFullAnalysisBDD().execute(bdd_model).get_result()
        signal.alarm(0)

        total_time = timer.Timer.timers[TIME_ANALYSIS]
        total_time = round(total_time, 4)
        print(f'{i}, {total_time}')
        stats_results.append(total_time)

    n_configs = result[FMFullAnalysisBDD.CONFIGURATIONS_NUMBER]
    core_features = result[FMFullAnalysisBDD.CORE_FEATURES]
    dead_features = result[FMFullAnalysisBDD.DEAD_FEATURES]
    print(f'#Configurations: {n_configs} ({utils.int_to_scientific_notation(n_configs)})')
    print(f'#Core features: {len(core_features)} {[f for f in core_features]}')
    print(f'#Dead features: {len(dead_features)} {[f for f in dead_features]}')

    # total_time = timer.Timer.timers[TIME_ANALYSIS]
    # total_time = round(total_time, 4)
    values_median = statistics.median(stats_results)
    values_mean = statistics.mean(stats_results)
    values_stdev = statistics.stdev(stats_results) if len(stats_results) > 1 else 0


    print(f'Time median (analysis): {values_median} s.')
    print(f'Model, Time_median(s), Time_mean(s), Time_stdev(s)')
    print(f'{filename}, {values_median}, {values_mean}, {values_stdev}')
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyze an FM using the BDD solver.')
    input_model = parser.add_mutually_exclusive_group(required=True)
    input_model.add_argument('-d', '--dir', dest='dir', type=str, help='Input directory with the models in the same format (.uvl or .json) to be analyzed.')
    input_model.add_argument('-fm', '--featuremodel', dest='feature_model', type=str, help='Input feature model in UVL format (.uvl).')
    parser.add_argument('-c', '--cores', dest='n_cores', type=int, required=False, default=1, help='Number of cores (processes) to execute (power of 2) (default = CPU count).')
    parser.add_argument('-r', '--runs', dest='runs', type=int, required=False, default=1, help='Number of experiments.')
    args = parser.parse_args()

    if args.n_cores <= 0 or not math.log(args.n_cores, 2).is_integer():
        if args.n_cores == multiprocessing.cpu_count():
            sys.exit(f'The number of cores of this computer is not a power of 2. Please set the -c parameter to a power of 2.')
        else:
            sys.exit(f'The number of cores must be positive and power of 2.')
    if not args.feature_model.endswith('.uvl'):
        sys.exit(f'Error, incorrect file format for {args.feature_model}. It should be a UVL model (.uvl).')

    main(args.feature_model, args.n_cores, args.runs)
