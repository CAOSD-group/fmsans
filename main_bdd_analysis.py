import os
import argparse

from flamapy.metamodels.fm_metamodel.transformations import UVLReader

from flamapy.metamodels.bdd_metamodel.transformations import FmToBDD
from flamapy.metamodels.bdd_metamodel.operations import (
    BDDProductsNumber,
    BDDCoreFeatures,
    BDDDeadFeatures
)

from fm_solver.utils import timer, memory_profiler, sizer


CODES = ['Reading', 'Transformation', 'ConfigNumber_op', 'CoreFeatures_op', 'DeadFeatures_op']


def main(fm_filepath: str) -> None:
    # Get feature model name
    fm_name = '.'.join(os.path.basename(fm_filepath).split('.')[:-1])

    # Load the feature model
    with memory_profiler.MemoryProfiler(name=CODES[0], logger=None), timer.Timer(name=CODES[0], logger=None):
        feature_model = UVLReader(fm_filepath).transform()

    fm_memory = sizer.getsizeof(feature_model, logger=None)

    # Create the BDD from the FM
    with memory_profiler.MemoryProfiler(name=CODES[1], logger=None), timer.Timer(name=CODES[1], logger=None):
        bdd_model = FmToBDD(feature_model).transform()

    bddmodel_memory = sizer.getsizeof(bdd_model, logger=None)

    # Products numbers
    with memory_profiler.MemoryProfiler(name=CODES[2], logger=None), timer.Timer(name=CODES[2], logger=None):
        n_configs = BDDProductsNumber().execute(bdd_model).get_result()
    print(f'#Configs: {n_configs}')

    # Core features
    with memory_profiler.MemoryProfiler(name=CODES[3], logger=None), timer.Timer(name=CODES[3], logger=None):
        core_features = BDDCoreFeatures().execute(bdd_model).get_result()
    print(f'Core features: {len(core_features)} {core_features}')

    # Dead features
    with memory_profiler.MemoryProfiler(name=CODES[4], logger=None), timer.Timer(name=CODES[4], logger=None):
        dead_features = BDDDeadFeatures().execute(bdd_model).get_result()
    print(f'Dead features: {len(dead_features)} {dead_features}')

    # Print outputs
    header = f"Features,Constraints,FM_size(B),BDD_size(B),{','.join(c + '(s)' for c in CODES)},{','.join(c + '(B)' for c in CODES)},#Configs,#Cores,Cores,#Deads,Deads"
    values = f'{len(feature_model.get_features())},{len(feature_model.get_constraints())},{fm_memory},{bddmodel_memory},'
    values += ','.join([str(timer.Timer.timers[c]) for c in CODES])
    values += ',' + ','.join([str(memory_profiler.MemoryProfiler.memory_profilers[c]) for c in CODES])
    values += f',{n_configs}'
    values += f',{len(core_features)},"{core_features}"'
    values += f',{len(dead_features)},"{dead_features}"'
    print(header)
    print(values)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyze an FM using the BDD Solver.')
    parser.add_argument('-fm', '--featuremodel', dest='feature_model', type=str, required=True, help='Input feature model in UVL format (.uvl).')
    args = parser.parse_args()

    main(args.feature_model)
    