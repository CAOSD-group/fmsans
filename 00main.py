import os
import argparse

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


def main(fm_filepath: str):
    # Get feature model name
    path, filename = os.path.split(fm_filepath)
    filename = ''.join(filename.split('.')[:-1])

    # Load the feature model
    print(f'Reading FM model... {fm_filepath}')
    feature_model = UVLReader(fm_filepath).transform()
    fm = FM.from_feature_model(feature_model)
    
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
    print(f'Time (refactorings): {total_time} s.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert an FM in (.uvl) to an FM in (.uvl) with only simple constraints (requires and excludes).')
    parser.add_argument('-fm', '--featuremodel', dest='feature_model', type=str, required=True, help='Input feature model in UVL format.')
    args = parser.parse_args()

    main(args.feature_model)

    print(f'Tip: Use the 01main.py script to convert the result FM to FMSans.')
    