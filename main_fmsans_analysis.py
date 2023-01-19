import os
import argparse
import time

from flamapy.metamodels.fm_metamodel.transformations import UVLReader, UVLWriter

from fm_solver.transformations import FMToFMSans, FMSansWriter, FMSansReader
from fm_solver.utils import fm_utils, logging_utils, timer, sizer
from fm_solver.models.feature_model import FM
from fm_solver.models import fm_sans as fm_sans_utils
from fm_solver.operations import FMConfigurationsNumber, FMConfigurations, FMCoreFeatures, FMFullAnalysis
from flamapy.metamodels.pysat_metamodel.operations import SATCoreFeatures
from flamapy.metamodels.pysat_metamodel.transformations import FmToPysat


NS_TO_MS = 1e-6


def main(fm_filepath: str) -> None:
    # Get feature model name
    logging_utils.FM_LOGGER.info(f'Input model: {fm_filepath}')
    fm_name = '.'.join(os.path.basename(fm_filepath).split('.')[:-1])
    logging_utils.FM_LOGGER.info(f'FM name: {fm_name}')

    # Load the feature model
    logging_utils.LOGGER.info(f"Reading FM '{fm_filepath}' model...")
    with timer.Timer(logger=logging_utils.LOGGER.info, message="FM loading."):
        feature_model = UVLReader(fm_filepath).transform()
        fm = FM.from_feature_model(feature_model)
    sizer.getsizeof(fm, logging_utils.LOGGER.info, message="FM.")
    #logging_utils.FM_LOGGER.info(fm_sans_utils.fm_stats(fm))
    
    if fm.get_constraints():
        print(f"Error: The FM has cross-tree constraints. Please transform it first using the 'fmsimplectcs2fmsans.py' script.")
        return None

    n_configurations = FMConfigurationsNumber().execute(fm).get_result()
    print(f'#Configurations: {n_configurations}')

    configurations = FMConfigurations().execute(fm).get_result()
    for i, c in enumerate(configurations, 1):
        print(f'C{i}: {[f.name for f in c.get_selected_elements()]}')

    core_features = FMCoreFeatures().execute(fm).get_result()
    print(f'Core features: {len(core_features)}, {[f.name for f in core_features]}')


def main_fmsans(fm_filepath: str) -> None:
    fm_sans = FMSansReader(fm_filepath).transform()
    result = fm_sans.get_analysis()
    fm = fm_sans.get_feature_model()
    subtrees = fm_sans.get_subtrees()

    # Execution time for core features
    start_time = time.perf_counter_ns()
    core_features = FMCoreFeatures().execute(fm).get_result()
    end_time = time.perf_counter_ns()
    elapsed_time = (end_time - start_time) * NS_TO_MS
    print(f'Core features (full model): {[f.name for f in core_features]}')
    print(f'Time (full model): {elapsed_time} ms')    

    # Execution time for core features
    start_time = time.perf_counter_ns()
    core_features = set.intersection(*[FMCoreFeatures().execute(t).get_result() for t in subtrees])
    end_time = time.perf_counter_ns()
    elapsed_time = (end_time - start_time) * NS_TO_MS
    print(f'Core features (subtrees: {len(subtrees)}): {[f.name for f in core_features]}')
    print(f'Time (subtrees: {len(subtrees)}): {elapsed_time} ms')    

    # Execution time for core features
    start_time = time.perf_counter_ns()
    core_features = fm_sans.get_core_features(n_processes=16)
    end_time = time.perf_counter_ns()
    elapsed_time = (end_time - start_time) * NS_TO_MS
    print(f'Core features (parallel): {[f.name for f in core_features]}')
    print(f'Time (parallel): {elapsed_time} ms')    

    # Execution time for core features
    sat_subtrees = [FmToPysat(t).transform() for t in subtrees]
    start_time = time.perf_counter_ns()
    core_features = set.intersection(*[SATCoreFeatures().execute(t).get_result() for t in sat_subtrees])
    end_time = time.perf_counter_ns()
    elapsed_time = (end_time - start_time) * NS_TO_MS
    print(f'Core features (subtrees SAT: {len(subtrees)}): {[f for f in core_features]}')
    print(f'Time (subtrees SAT: {len(subtrees)}): {elapsed_time} ms')    

   

    # raise Exception
    # print(f'Result from paralelization analysis: ')
    # print(f'#Configurations: {result[FMFullAnalysis.CONFIGURATIONS_NUMBER]}')
    # print(f'Core features: {len(result[FMFullAnalysis.CORE_FEATURES])}, {[f.name for f in result[FMFullAnalysis.CORE_FEATURES]]}')

    # fm = fm_sans.get_feature_model()
    # print(f'Result from full composed feature model: ')
    # n_configurations = FMConfigurationsNumber().execute(fm).get_result()
    # print(f'#Configurations: {n_configurations}')

    # core_features = FMCoreFeatures().execute(fm).get_result()
    # print(f'Core features: {len(core_features)}, {[f.name for f in core_features]}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyze an FM using the FM Solver.')
    input_model = parser.add_mutually_exclusive_group(required=True)
    input_model.add_argument('-fm', '--featuremodel', dest='feature_model', type=str, help='Input feature model in UVL format (.uvl).')
    input_model.add_argument('-fmsans', dest='fm_sans', type=str, help='Input feature model in FMSans (.json) format.')
    args = parser.parse_args()

    if args.feature_model:
        main(args.feature_model)
    elif args.fm_sans:
        main_fmsans(args.fm_sans) 
        pass
    