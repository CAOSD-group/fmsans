import os
import sys
import argparse
import statistics

from flamapy.metamodels.fm_metamodel.transformations import UVLReader

from fm_solver.utils import utils,timer, sizer, memory_profiler
from fm_solver.operations import (
    FMConfigurationsNumber, FMCoreFeatures, FMFullAnalysis
)

OUTPUT_DIR = 'results'
OUTPUTFILE_RESULTS_STATS = 'step7_stats'
TIME_ANALYSIS = 'TIME_ANALYSIS'
MEMORY_ANALYSIS = 'MEMORY_ANALYSIS'


def get_fm_filepath_models(dir: str) -> list[str]:
    """Get all models from the given directory."""
    models = []
    for root, dirs, files in os.walk(dir):
        for file in files:
            filepath = os.path.join(root, file)
            models.append(filepath)
    return models


def main(fm_filepath: str, runs: int) -> None:
    # Get feature model name
    path, filename = os.path.split(fm_filepath)
    filename = '.'.join(filename.split('.')[:-1])

    # Output file for raw data
    output_dir = os.path.join(path, OUTPUT_DIR)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_file = os.path.join(path, OUTPUT_DIR, f'{filename}.csv')

    # Load the feature model
    print(f'  Reading FM model (.uvl) from {fm_filepath}...')
    fm = UVLReader(fm_filepath).transform()
    fm_memory = sizer.getsizeof(fm, logger=None) / 1e6
    print(f'Memory of the feature model (MB): {fm_memory}')
        
    # Perform analysis
    print(f'Analyzing model...')
    stats_results = []
    stats_results_mem = []
    with open(output_file, 'w', encoding='utf8') as file:
        file.write(f'Run, Time(s){os.linesep}')
        print(f'Run: ', end='', flush=True)
        for i in range(1, runs + 1):
            print(f'{i} ', end='', flush=True)

            with memory_profiler.MemoryProfiler(name=MEMORY_ANALYSIS, logger=None), timer.Timer(name=TIME_ANALYSIS, logger=None):
                result = FMFullAnalysis().execute(fm).get_result()

            total_time = timer.Timer.timers[TIME_ANALYSIS]
            total_time = round(total_time, 4)
            file.write(f'{i}, {total_time}{os.linesep}')
            stats_results.append(total_time)
            stats_results_mem.append(memory_profiler.MemoryProfiler.memory_profilers[MEMORY_ANALYSIS])
    print()

    # Get results
    n_configs = result[FMConfigurationsNumber.get_name()]
    n_configs_scientific = utils.int_to_scientific_notation(n_configs)
    n_configs_pretty = n_configs_scientific if n_configs > 10e6 else n_configs
    core_features = result[FMCoreFeatures.get_name()]
    #dead_features = result[FMDeadFeatures.get_name()]
    print(f'#Configurations: {n_configs} ({n_configs_scientific})')
    print(f'#Core features: {len(core_features)} {[f for f in core_features]}')
    #print(f'#Dead features: {len(dead_features)} {[f.name if isinstance(f, Feature) else f for f in dead_features]}')

    n_features = len(fm.get_features())
    n_ctcs = len(fm.get_constraints())

    # Get stats
    values_median = statistics.median(stats_results)
    values_mean = statistics.mean(stats_results)
    values_stdev = statistics.stdev(stats_results) if len(stats_results) > 1 else 0
    memory_median = statistics.median(stats_results_mem)
    pretty_memory = memory_median / 1e6  # MB
    print(f'Time median (analysis): {values_median} s.')
    print(f'Model, Runs, Features, Constraints, Products, CoreFeatures, Time_median(s), Time_mean(s), Time_stdev(s), Memory(MB)')
    print(f'{filename}, {runs}, {n_features}, {n_ctcs}, {n_configs_pretty}, {len(core_features)}, {values_median}, {values_mean}, {values_stdev}, {pretty_memory}')

    # Save stats in file
    outputfile_stats = os.path.join(path, OUTPUT_DIR, f'{OUTPUTFILE_RESULTS_STATS}.csv')
    if not os.path.exists(outputfile_stats):
        with open(outputfile_stats, 'w', encoding='utf8') as file:
            file.write(f'Model, Runs, Features, Constraints, Products, CoreFeatures, Time_median(s), Time_mean(s), Time_stdev(s), Memory(MB){os.linesep}')
    with open(outputfile_stats, 'a', encoding='utf8') as file:
        file.write(f'{filename}, {runs}, {n_features}, {n_ctcs}, {n_configs_pretty}, {len(core_features)}, {values_median}, {values_mean}, {values_stdev}, {pretty_memory}{os.linesep}')
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyze a generalized feature tree (GFT) in UVL format (.uvl).')
    input_model = parser.add_mutually_exclusive_group(required=True)
    input_model.add_argument('-d', '--dir', dest='dir', type=str, help='Input directory with the models in the same format (.uvl or .json) to be analyzed.')
    input_model.add_argument('-fm', '--featuremodel', dest='feature_model', type=str, help='Input feature model in UVL (.uvl) or FMSans (.json) format.')
    parser.add_argument('-r', '--runs', dest='runs', type=int, required=False, default=1, help='Number of experiments.')
    args = parser.parse_args()

    if args.feature_model:    
        if not args.feature_model.endswith('.uvl'):
            sys.exit(f'Error, incorrect file format for {args.feature_model}. It should be a UVL (.uvl) model.')
        main(args.feature_model, args.runs)

    elif args.dir:
        models = get_fm_filepath_models(args.dir)
        for filepath in models:
            if not filepath.endswith('.uvl'):
                print(f'Skipped file: {filepath}')
            else:
                main(filepath, args.runs)
