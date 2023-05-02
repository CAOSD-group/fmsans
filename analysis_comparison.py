import os
import sys
import argparse
import statistics

from flamapy.metamodels.fm_metamodel.transformations import UVLReader
from flamapy.metamodels.pysat_metamodel.transformations import FmToPysat
from flamapy.metamodels.bdd_metamodel.transformations import FmToBDD

from fm_solver.utils import timer
from fm_solver.operations import (
    FMConfigurationsNumber, 
    FMCoreFeatures, 
    FMDeadFeatures,
    FMDeadFeaturesGFT,
    FMValid
)

from flamapy.metamodels.bdd_metamodel.operations import (
    BDDProductsNumber,
    BDDCoreFeatures,
    BDDDeadFeatures,
    BDDValid
)

from flamapy.metamodels.pysat_metamodel.operations import (
    SATProductsNumber,
    SATCoreFeatures,
    SATDeadFeatures,
    Glucose3Valid
)


OUTPUT_DIR = 'results'
OUTPUTFILE_RESULTS_STATS = 'analysis'
TIME_ANALYSIS = 'TIME_ANALYSIS'
TOOLS = ['sat', 'bdd', 'gft']
OPERATION = 'DeadFeatures'

def get_fm_filepath_models(dir: str) -> list[str]:
    """Get all models from the given directory."""
    models = []
    for root, dirs, files in os.walk(dir):
        for file in files:
            filepath = os.path.join(root, file)
            models.append(filepath)
    return models


def main(fm_filepath: str, runs: int, tool: str) -> None:
    # Get feature model name
    path, filename = os.path.split(fm_filepath)
    filename = '.'.join(filename.split('.')[:-1])

    # Output file for raw data
    output_dir = os.path.join(path, OUTPUT_DIR)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_file = os.path.join(path, OUTPUT_DIR, f'{filename}_{tool}_{OPERATION}.csv')

    # Load the feature model
    print(f'Reading feature model from {fm_filepath}')
    fm = None
    sat_model = None
    bdd_model = None
    
    print(f'  Reading FM model (.uvl)...')
    fm = UVLReader(fm_filepath).transform()
        
    if tool == 'sat':
        print(f'    Transforming feature model to SAT...')
        sat_model = FmToPysat(fm).transform()

    elif tool == 'bdd':
        print(f'    Transforming feature model to BDD...')
        bdd_model = FmToBDD(fm).transform()
        
    # Perform analysis
    print(f'Analyzing model...')
    stats_results = []
    with open(output_file, 'w', encoding='utf8') as file:
        file.write(f'Run, Time(s){os.linesep}')
        print(f'Run: ', end='', flush=True)
        for i in range(1, runs + 1):
            print(f'{i} ', end='', flush=True)

            op_model_dict = {'sat': (SATProductsNumber(), sat_model),
                             'bdd': (BDDDeadFeatures(), bdd_model),
                             'gft': (FMDeadFeaturesGFT(), fm)}
            
            op, model = op_model_dict[tool]
            with timer.Timer(name=TIME_ANALYSIS, logger=None):
                result = op.execute(model).get_result()

            total_time = timer.Timer.timers[TIME_ANALYSIS]
            total_time = round(total_time, 4)
            file.write(f'{i}, {total_time}{os.linesep}')
            stats_results.append(total_time)
    print()

    # Get results
    print(result)
    
    # n_configs = result[FMConfigurationsNumber.get_name()]
    # n_configs_scientific = utils.int_to_scientific_notation(n_configs)
    # n_configs_pretty = n_configs_scientific if n_configs > 10e6 else n_configs
    # core_features = result[FMCoreFeatures.get_name()]
    # #dead_features = result[FMDeadFeatures.get_name()]
    # print(f'#Configurations: {n_configs} ({n_configs_scientific})')
    # print(f'#Core features: {len(core_features)} {[f for f in core_features]}')
    # #print(f'#Dead features: {len(dead_features)} {[f.name if isinstance(f, Feature) else f for f in dead_features]}')

    n_features = len(fm.get_features())
    n_ctcs = len(fm.get_constraints())
    # Get stats
    values_median = statistics.median(stats_results)
    values_mean = statistics.mean(stats_results)
    values_stdev = statistics.stdev(stats_results) if len(stats_results) > 1 else 0
    print(f'Time median (analysis): {values_median} s.')
    print(f'Model, Tool, Runs, Features, Constraints, Time_median(s), Time_mean(s), Time_stdev(s)')
    print(f'{filename}, {tool}, {runs}, {n_features}, {n_ctcs}, {values_median}, {values_mean}, {values_stdev}')

    # Save stats in file
    outputfile_stats = os.path.join(path, OUTPUT_DIR, f'{OUTPUTFILE_RESULTS_STATS}_{tool}_{OPERATION}.csv')
    if not os.path.exists(outputfile_stats):
        with open(outputfile_stats, 'w', encoding='utf8') as file:
            file.write(f'Model, Tool, Runs, Features, Constraints, Time_median(s), Time_mean(s), Time_stdev(s){os.linesep}')
    with open(outputfile_stats, 'a', encoding='utf8') as file:
        file.write(f'{filename}, {tool}, {runs}, {n_features}, {n_ctcs}, {values_median}, {values_mean}, {values_stdev}{os.linesep}')
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyze an FM using different solvers.')
    input_model = parser.add_mutually_exclusive_group(required=True)
    input_model.add_argument('-d', '--dir', dest='dir', type=str, help='Input directory with the models in the same format (.uvl) to be analyzed.')
    input_model.add_argument('-fm', '--featuremodel', dest='feature_model', type=str, help='Input feature model in UVL (.uvl) format.')
    parser.add_argument('-r', '--runs', dest='runs', type=int, required=False, default=1, help='Number of experiments.')
    parser.add_argument('-t', '--tool', dest='tool', type=str, required=False, default='fmsans', help=f'Tool to execute {TOOLS} (default fmsans).')
    args = parser.parse_args()

    if args.feature_model:    
        if not args.feature_model.endswith('.uvl'):
            sys.exit(f'Error, incorrect file format for {args.feature_model}. It should be a UVL (.uvl) model.')
        if args.tool not in TOOLS:
            sys.exit(f'Error, incorrect tool to execute. Use one of {TOOLS}.')

        main(args.feature_model, args.runs, args.tool)

    elif args.dir:
        models = get_fm_filepath_models(args.dir)
        if not all(filepath.endswith('.uvl') for filepath in models):
           print(f'Warning, the directory contains other files. They will be ignored.')

        for filepath in models:
            if not filepath.endswith('.uvl') and not filepath.endswith('.json'):
                print(f'Skipped file: {filepath}')
            else:
                main(filepath, args.runs, args.tool)
            

