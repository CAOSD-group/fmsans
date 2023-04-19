import os
import argparse
import signal

from flamapy.metamodels.fm_metamodel.transformations import UVLReader, UVLWriter

from fm_solver.models.feature_model import FM
from fm_solver.utils import utils, constraints_utils
from fm_solver.transformations.refactorings import (
    RefactoringPseudoComplexConstraint,
    RefactoringStrictComplexConstraint
)

from fm_solver.utils import timer


FM_OUTPUT_FILENAME_POSTFIX = '_simple'
TIME_PSEUDO_COMPLEX_CTCS = 'TIME_PSEUDO_COMPLEX_CTCS'
TIME_STRICT_COMPLEX_CTCS = 'TIME_STRICT_COMPLEX_CTCS'

TIME_OUT = 360000  # seconds
OUTPUT_FILE = 'step1_stats.csv'


def timeout_handler(signum, frame):
    """Use a system signal to check out time outs."""
    raise Exception(f'Time out! ({TIME_OUT} seconds)')
signal.signal(signal.SIGALRM, timeout_handler)


def get_fm_filepath_models(dir: str) -> list[str]:
    """Get all models from the given directory."""
    models = []
    for root, dirs, files in os.walk(dir):
        for file in files:
            filepath = os.path.join(root, file)
            models.append(filepath)
    return models


def main(fm_filepath: str):
    # Get feature model name
    path, filename = os.path.split(fm_filepath)
    filename = ''.join(filename.split('.')[:-1])

    # Output file for raw data
    output_file = os.path.join(path, OUTPUT_FILE)

    # Load the feature model
    print(f'Reading feature model from {fm_filepath}')
    feature_model = UVLReader(fm_filepath).transform()
    fm = FM.from_feature_model(feature_model)
    n_features = len(fm.get_features())
    n_ctcs = len(fm.get_constraints())
    
    # Check if the feature model has any cross-tree constraints
    if not any(constraints_utils.is_complex_constraint(ctc) for ctc in fm.get_constraints()):
        print(f'Warning: The feature model has not any complex cross-tree constraints. The output FM is the same as the input.')

    # Refactor pseudo-complex constraints
    print(f'Refactoring pseudo-complex constraints...')
    with timer.Timer(name=TIME_PSEUDO_COMPLEX_CTCS, logger=None):
        fm = utils.apply_refactoring(fm, RefactoringPseudoComplexConstraint)
    
    # Refactor strict-complex constraints
    print(f'Refactoring strict-complex constraints...')
    with timer.Timer(name=TIME_STRICT_COMPLEX_CTCS, logger=None):
        fm = utils.apply_refactoring(fm, RefactoringStrictComplexConstraint)

    # Serializing the feature model
    output_fm_filepath = f'{filename}{FM_OUTPUT_FILENAME_POSTFIX}.uvl'
    print(f'Serializing FM model in {output_fm_filepath} ...')
    UVLWriter(path=output_fm_filepath, source_model=fm).transform()

    total_time = timer.Timer.timers[TIME_PSEUDO_COMPLEX_CTCS] + timer.Timer.timers[TIME_STRICT_COMPLEX_CTCS]
    total_time = round(total_time, 4)
    print(f'Time (refactorings): {total_time} s.')

    # Save stats in file
    if not os.path.exists(output_file):
        with open(output_file, 'w', encoding='utf8') as file:
            file.write(f'Model, F, CTC, Time(s){os.linesep}')
    with open(output_file, 'a', encoding='utf8') as file:
        file.write(f'{filename}, {n_features}, {n_ctcs}, {total_time}{os.linesep}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert an FM in (.uvl) to an FM in (.uvl) with only simple constraints (requires and excludes).')
    input_model = parser.add_mutually_exclusive_group(required=True)
    input_model.add_argument('-d', '--dir', dest='dir', type=str, help='Input directory with the models in the same format (.uvl or .json) to be analyzed.')
    input_model.add_argument('-fm', '--featuremodel', dest='feature_model', type=str, help='Input feature model in UVL format.')
    args = parser.parse_args()

    if args.feature_model:
        main(args.feature_model)
    elif args.dir:
        models = get_fm_filepath_models(args.dir)
        for filepath in models:
            if filepath.endswith('.uvl'):
                main(filepath)

    print(f'Tip: Use the 01main.py script to convert the result FM to FMSans.')
    