import os
import sys
import math
import argparse
import multiprocessing

from flamapy.metamodels.fm_metamodel.transformations import UVLReader
from flamapy.metamodels.fm_metamodel.models import Feature

from fm_solver.transformations import FMToFMSans, FMSansReader
from fm_solver.operations.fmsans_op import (
    FMSansProductsNumber,
    FMSansCoreFeatures,
    FMSansDeadFeatures,
    FMSansFullAnalysis
)

from fm_solver.utils import timer, memory_profiler, sizer


CODES = ['Reading', 'Transformation', 'ProductsNumber_op', 'CoreFeatures_op', 'DeadFeatures_op']
#CODES = ['Reading', 'Transformation', 'FullAnalysis_op']


def main(fm_filepath: str, n_cores: int) -> None:
    # Get feature model name
    path, filename = os.path.split(fm_filepath)
    filename = '.'.join(filename.split('.')[:-1])

    # Read the FM Sans
    with memory_profiler.MemoryProfiler(name=CODES[0], logger=None), timer.Timer(name=CODES[0], logger=None):
        fmsans_model = FMSansReader(fm_filepath).transform()

    # there is not transformation needed.
    with memory_profiler.MemoryProfiler(name=CODES[1], logger=None), timer.Timer(name=CODES[1], logger=None):
        pass
    
    fm_memory = sizer.getsizeof(fmsans_model, logger=None)
    n_features = len(fmsans_model.fm.get_features())
    n_constraints = len(fmsans_model.fm.get_constraints())

    # Products numbers
    with memory_profiler.MemoryProfiler(name=CODES[2], logger=None), timer.Timer(name=CODES[2], logger=None):
        n_configs = fmsans_model.get_number_of_configurations_bdd(n_cores)
    print(f'#Configs: {n_configs}')

    # Core features
    with memory_profiler.MemoryProfiler(name=CODES[3], logger=None), timer.Timer(name=CODES[3], logger=None):
        core_features = fmsans_model.get_core_features_bdd(n_cores)
    if core_features and isinstance(core_features[0], Feature):
        core_features = [f.name for f in core_features]
    print(f'Core features: {len(core_features)} {[f for f in core_features]}')

    # Dead features
    with memory_profiler.MemoryProfiler(name=CODES[4], logger=None), timer.Timer(name=CODES[4], logger=None):
        dead_features = []
    if dead_features and isinstance(dead_features[0], Feature):
        dead_features = [f.name for f in dead_features]
    print(f'Dead features: {len(dead_features)} {[f for f in dead_features]}')

    # Print outputs
    header = f"Parallel_cores,Features,Constraints,FM_size(B),{','.join(c + '(s)' for c in CODES)},{','.join(c + '(B)' for c in CODES)},#Configs,#Cores,Cores,#Deads,Deads"
    values = f'{n_cores},{n_features},{n_constraints},{fm_memory},'
    values += ','.join([str(timer.Timer.timers[c]) for c in CODES])
    values += ',' + ','.join([str(memory_profiler.MemoryProfiler.memory_profilers[c]) for c in CODES])
    values += f',{n_configs}'
    values += f',{len(core_features)},"{[f for f in core_features]}"'
    values += f',{len(dead_features)},"{[f for f in dead_features]}"'
    print(header)
    print(values)


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

    