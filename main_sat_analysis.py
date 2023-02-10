import os
import argparse

from flamapy.metamodels.fm_metamodel.transformations import UVLReader

from flamapy.metamodels.pysat_metamodel.transformations import FmToPysat
from flamapy.metamodels.pysat_metamodel.operations import SATCoreFeatures, SATDeadFeatures

from fm_solver.utils import timer, memory_profiler, sizer


SOLVER_NAMES = """
            cadical     = ('cd', 'cdl', 'cadical')
            gluecard3   = ('gc3', 'gc30', 'gluecard3', 'gluecard30')
            gluecard41  = ('gc3', 'gc41', 'gluecard4', 'gluecard41')
            glucose3    = ('g3', 'g30', 'glucose3', 'glucose30')
            glucose4    = ('g4', 'g41', 'glucose4', 'glucose41')
            lingeling   = ('lgl', 'lingeling')
            maplechrono = ('mcb', 'chrono', 'maplechrono')
            maplecm     = ('mcm', 'maplecm')
            maplesat    = ('mpl', 'maple', 'maplesat')
            mergesat3   = ('mg3', 'mgs3', 'mergesat3', 'mergesat30')
            minicard    = ('mc', 'mcard', 'minicard')
            minisat22   = ('m22', 'msat22', 'minisat22')
            minisatgh   = ('mgh', 'msat-gh', 'minisat-gh')
"""

CODES = ['Reading', 'Transformation', 'CoreFeatures_op', 'DeadFeatures_op']


def main(fm_filepath: str, solver_name: str) -> None:
    # Get feature model name
    fm_name = '.'.join(os.path.basename(fm_filepath).split('.')[:-1])

    # Load the feature model
    with memory_profiler.MemoryProfiler(name=CODES[0], logger=None), timer.Timer(name=CODES[0], logger=None):
        feature_model = UVLReader(fm_filepath).transform()

    fm_memory = sizer.getsizeof(feature_model, logger=None)

    # Create the BDD from the FM
    with memory_profiler.MemoryProfiler(name=CODES[1], logger=None), timer.Timer(name=CODES[1], logger=None):
        sat_model = FmToPysat(feature_model).transform()

    satmodel_memory = sizer.getsizeof(sat_model, logger=None)

    # Core features
    with memory_profiler.MemoryProfiler(name=CODES[2], logger=None), timer.Timer(name=CODES[2], logger=None):
        core_features = SATCoreFeatures(solver_name).execute(sat_model).get_result()
    print(f'Core features: {len(core_features)} {core_features}')

    # Dead features
    with memory_profiler.MemoryProfiler(name=CODES[3], logger=None), timer.Timer(name=CODES[3], logger=None):
        dead_features = SATDeadFeatures(solver_name).execute(sat_model).get_result()
    print(f'Dead features: {len(dead_features)} {dead_features}')

    # Print outputs
    header = f"FM_size(B),SAT_size(B),{','.join(c + '(s)' for c in CODES)},{','.join(c + '(B)' for c in CODES)},#Cores,Cores,#Deads,Deads"
    values = f'{fm_memory},{satmodel_memory},'
    values += ','.join([str(timer.Timer.timers[c]) for c in CODES])
    values += ',' + ','.join([str(memory_profiler.MemoryProfiler.memory_profilers[c]) for c in CODES])
    values += f',{len(core_features)},"{core_features}"'
    values += f',{len(dead_features)},"{dead_features}"'
    print(header)
    print(values)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyze an FM using the SAT Solver.')
    parser.add_argument('-fm', '--featuremodel', dest='feature_model', type=str, required=True, help='Input feature model in UVL format (.uvl).')
    parser.add_argument('-s', '--solver', dest='solver', type=str, required=False, default='glucose3', help='Solver to use (default "glucose3").' + SOLVER_NAMES)
    args = parser.parse_args()

    main(args.feature_model, args.solver)
    