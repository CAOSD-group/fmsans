import os
import argparse
import multiprocessing

from flamapy.metamodels.fm_metamodel.transformations import UVLReader

from fm_solver.transformations import FMToFMSans
from fm_solver.operations.fmsans_op import (
    FMSansProductsNumber,
    FMSansCoreFeatures,
    FMSansDeadFeatures
)

from fm_solver.utils import timer, memory_profiler, sizer


CODES = ['Reading', 'Transformation', 'ProductsNumber_op', 'CoreFeatures_op', 'DeadFeatures_op']


def main(fm_filepath: str) -> None:
    # Get feature model name
    fm_name = '.'.join(os.path.basename(fm_filepath).split('.')[:-1])

    n_cores = multiprocessing.cpu_count()

    # Load the feature model
    with memory_profiler.MemoryProfiler(name=CODES[0], logger=None), timer.Timer(name=CODES[0], logger=None):
        feature_model = UVLReader(fm_filepath).transform()

    fm_memory = sizer.getsizeof(feature_model, logger=None)
    n_features = len(feature_model.get_features())
    n_constraints = len(feature_model.get_constraints())

    # Create the BDD from the FM
    with memory_profiler.MemoryProfiler(name=CODES[1], logger=None), timer.Timer(name=CODES[1], logger=None):
        fmsans_model = FMToFMSans(source_model=feature_model, n_cores=n_cores).transform()

    print(fmsans_model)
    fmsansmodel_memory = sizer.getsizeof(fmsans_model, logger=None)

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
    parser = argparse.ArgumentParser(description='Analyze an FM using the BDD Solver.')
    parser.add_argument('-fm', '--featuremodel', dest='feature_model', type=str, required=True, help='Input feature model in UVL format (.uvl).')
    args = parser.parse_args()

    main(args.feature_model)
    