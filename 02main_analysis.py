import os
import sys
import math
import argparse
import time
import multiprocessing

from flamapy.metamodels.fm_metamodel.transformations import UVLReader, UVLWriter

from fm_solver.transformations import FMToFMSans, FMSansWriter, FMSansReader
from fm_solver.utils import utils, fm_utils, logging_utils, timer, sizer
from fm_solver.models.feature_model import FM
from fm_solver.models import fm_sans as fm_sans_utils
from fm_solver.operations import FMConfigurationsNumber, FMConfigurations, FMCoreFeatures, FMFullAnalysis
from flamapy.metamodels.pysat_metamodel.operations import SATCoreFeatures
from flamapy.metamodels.pysat_metamodel.transformations import FmToPysat


TIME_ANALYSIS = 'TIME_ANALYSIS'


def main(fm_filepath: str, n_cores: int) -> None:
    # Get feature model name
    path, filename = os.path.split(fm_filepath)
    filename = ''.join(filename.split('.')[:-1])

    # Load the feature model (FMSans)
    print(f'Reading FMSans model... {fm_filepath}')
    fmsans_model = FMSansReader(fm_filepath).transform()

    # Perform full analysis of FMSans
    print(f'Analyzing FMSans model with {len(fmsans_model.transformations_ids)} subtrees...')
    with timer.Timer(name=TIME_ANALYSIS, logger=None):
        result = fmsans_model.get_analysis(n_cores)

    n_configs = result[FMFullAnalysis.CONFIGURATIONS_NUMBER]
    core_features = result[FMFullAnalysis.CORE_FEATURES]
    print(f'#Configurations: {n_configs} ({utils.int_to_scientific_notation(n_configs)})')
    print(f'#Core features: {len(core_features)} {[f.name for f in core_features]}')

    print(f'Time (analysis): {timer.Timer.timers[TIME_ANALYSIS]} s.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyze an FM using the FMSans Solver.')
    parser.add_argument('-fm', '--featuremodel', dest='feature_model', type=str, required=True, help='Input feature model in FMSans format (.json).')
    parser.add_argument('-c', '--cores', dest='n_cores', type=int, required=False, default=multiprocessing.cpu_count(), help='Number of cores (processes) to execute (power of 2) (default = CPU count).')
    args = parser.parse_args()

    if args.n_cores <= 0 or not math.log(args.n_cores, 2).is_integer():
        if args.n_cores == multiprocessing.cpu_count():
            sys.exit(f'The number of cores of this computer is not a power of 2. Please set the -c parameter to a power of 2.')
        else:
            sys.exit(f'The number of cores must be positive and power of 2.')
    if not args.feature_model.endswith('.json'):
        sys.exit(f'Error, incorrect file format for {args.feature_model}. It should be a FMSans model (.json).')

    main(args.feature_model, args.n_cores)
