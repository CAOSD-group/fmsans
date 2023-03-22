import os
import sys
import argparse
import multiprocessing
import math

from flamapy.metamodels.fm_metamodel.transformations import UVLReader

from fm_solver.models.feature_model import FM
from fm_solver.transformations import FMToFMSans
from fm_solver.utils import utils, constraints_utils

from fm_solver.operations import (
    FMFullAnalysis,
)

from fm_solver.transformations import FMSansWriter
from fm_solver.utils import timer

FM_OUTPUT_FILENAME_POSTFIX = '_fmsans'
TIME_TRANSFORMATION = 'TIME_TRANSFORMATION'


def get_fm_filepath_models(dir: str) -> list[str]:
    """Get all models from the given directory."""
    models = []
    for root, dirs, files in os.walk(dir):
        for file in files:
            filepath = os.path.join(root, file)
            models.append(filepath)
    return models


def main(fm_filepath: str, n_cores: int, n_tasks: int = 1, current_task: int = 1):
    # Get feature model name
    path, filename = os.path.split(fm_filepath)
    filename = ''.join(filename.split('.')[:-1])

    # Load the feature model
    print(f'Reading FM model... {fm_filepath}')
    feature_model = UVLReader(fm_filepath).transform()
    fm = FM.from_feature_model(feature_model)

    # Check if the feature model has any cross-tree constraints
    if any(constraints_utils.is_complex_constraint(ctc) for ctc in fm.get_constraints()):
        print(f'Warning: The feature model has complex cross-tree constraints. Use first the 00main.py script to refactor them, otherwise this may take even longer.')

    # Transform the feature model to FMSans
    print(f'Transforming FM model to FMSans (eliminating constraints)...')
    with timer.Timer(name=TIME_TRANSFORMATION, logger=None):
        fmsans_model = FMToFMSans(fm, n_cores=n_cores, n_tasks=n_tasks, current_task=current_task).transform()

    # Serializing the FMSans model
    output_fmsans_filepath = f'{filename}_{n_cores}_{current_task}-{n_tasks}.json'
    print(f'Serializing FMSans model in {output_fmsans_filepath} ...')
    FMSansWriter(output_fmsans_filepath, fmsans_model).transform()

    total_time = timer.Timer.timers[TIME_TRANSFORMATION]
    total_time = round(total_time, 4)
    print(f'Time (transformation): {total_time} s.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert an FM in (.uvl) to an FMSans (.json).')
    input_model = parser.add_mutually_exclusive_group(required=True)
    input_model.add_argument('-fm', '--featuremodel', dest='feature_model', type=str, help='Input feature model in UVL format.')
    input_model.add_argument('-d', '--dir', dest='dir', type=str, help='Input directory with the models in the same format (.uvl or .json) to be analyzed.')
    parser.add_argument('-c', '--cores', dest='n_cores', type=int, required=False, default=multiprocessing.cpu_count(), help='Number of cores (processes) to execute (power of 2) (default = CPU count).')
    parser.add_argument('-t', '--tasks', dest='n_tasks', type=int, required=False, default=1, help='Number of tasks.')
    parser.add_argument('-i', '--task', dest='current_task', type=int, required=False, default=0, help='Current task.')
    args = parser.parse_args()

    if args.n_cores <= 0 or not math.log(args.n_cores, 2).is_integer():
        if args.n_cores == multiprocessing.cpu_count():
            sys.exit(f'The number of cores of this computer is not a power of 2. Please set the -c parameter to a power of 2.')
        else:
            sys.exit(f'The number of cores must be positive and power of 2.')
    if args.n_tasks <= 0 or not math.log(args.n_tasks, 2).is_integer() and args.current_task >= 1 and args.current_task <= args.n_tasks:
        sys.exit(f'The number of tasks must be positive and power of 2.')
    else:
        if args.feature_model:
            main(args.feature_model, args.n_cores, args.n_tasks, args.current_task)
            print(f'Tip: Use the 02main_analysis.py script to analyze the result FMSans.')
        elif args.dir:
            models = get_fm_filepath_models(args.dir)
            for filepath in models:
                main(filepath, args.n_cores, args.n_tasks, args.current_task)

