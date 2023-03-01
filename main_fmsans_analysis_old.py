import os
import sys
import math
import argparse
import multiprocessing

from flamapy.metamodels.fm_metamodel.transformations import UVLReader

from fm_solver.transformations import FMToFMSans, FMSansReader
from fm_solver.operations.fmsans_op import (
    FMSansProductsNumber,
    FMSansCoreFeatures,
    FMSansDeadFeatures,
    FMSansFullAnalysis
)

from fm_solver.utils import timer, memory_profiler, sizer


CODES = ['Reading', 'Transformation', 'ProductsNumber_op', 'CoreFeatures_op', 'DeadFeatures_op']


def main(fm_filepath: str, n_cores: int) -> None:
    # Get feature model name
        # Get feature model name
    path, filename = os.path.split(fm_filepath)
    filename = '.'.join(filename.split('.')[:-1])

    # Load the feature model
    feature_model = None
    if fm_filepath.endswith('.uvl'):
        # Load the UVL model
        with memory_profiler.MemoryProfiler(name=CODES[0], logger=None), timer.Timer(name=CODES[0], logger=None):
            feature_model = UVLReader(fm_filepath).transform()

        fm_memory = sizer.getsizeof(feature_model, logger=None)
        n_features = len(feature_model.get_features())
        n_constraints = len(feature_model.get_constraints())

        # Create the FMSans from the FM (this may take a while)
        with memory_profiler.MemoryProfiler(name=CODES[1], logger=None), timer.Timer(name=CODES[1], logger=None):
            fmsans_model = FMToFMSans(source_model=feature_model, n_cores=n_cores).transform()

    elif fm_filepath.endswith('.json'):
        with memory_profiler.MemoryProfiler(name=CODES[0], logger=None), timer.Timer(name=CODES[0], logger=None):
            fmsans_model = FMSansReader(fm_filepath).transform()

        # there is not transformation needed.
        with memory_profiler.MemoryProfiler(name=CODES[1], logger=None), timer.Timer(name=CODES[1], logger=None):
            pass
    else:
        sys.exit(f'Error, incorrect file format for {fm_filepath}')

    if feature_model is None:
        fm_memory = 0
        n_features = 0
        n_constraints = 0

    fmsansmodel_memory = sizer.getsizeof(fmsans_model, logger=None)

    # Full analysis
    with memory_profiler.MemoryProfiler(name=CODES[2], logger=None), timer.Timer(name=CODES[2], logger=None):
        result = FMSansFullAnalysis(n_cores).execute(fmsans_model).get_result()

    # Products numbers
    with memory_profiler.MemoryProfiler(name=CODES[2], logger=None), timer.Timer(name=CODES[2], logger=None):
        n_configs = FMSansProductsNumber(n_cores).execute(fmsans_model).get_result()
    print(f'#Configs: {n_configs}')

    # Core features
    with memory_profiler.MemoryProfiler(name=CODES[3], logger=None), timer.Timer(name=CODES[3], logger=None):
        core_features = FMSansCoreFeatures(n_cores).execute(fmsans_model).get_result()
    print(f'Core features: {len(core_features)} {[f.name for f in core_features]}')

    # Dead features
    with memory_profiler.MemoryProfiler(name=CODES[4], logger=None), timer.Timer(name=CODES[4], logger=None):
        dead_features = FMSansDeadFeatures(n_cores).execute(fmsans_model).get_result()
    print(f'Dead features: {len(dead_features)} {[f.name for f in dead_features]}')

    # Print outputs
    header = f"Features,Constraints,FM_size(B),FMSans_size(B),{','.join(c + '(s)' for c in CODES)},{','.join(c + '(B)' for c in CODES)},#Configs,#Cores,Cores,#Deads,Deads"
    values = f'{n_features},{n_constraints},{fm_memory},{fmsansmodel_memory},'
    values += ','.join([str(timer.Timer.timers[c]) for c in CODES])
    values += ',' + ','.join([str(memory_profiler.MemoryProfiler.memory_profilers[c]) for c in CODES])
    values += f',{n_configs}'
    values += f',{len(core_features)},"{[f.name for f in core_features]}"'
    values += f',{len(dead_features)},"{[f.name for f in dead_features]}"'
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

    