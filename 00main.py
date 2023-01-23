import os
import argparse

from flamapy.metamodels.fm_metamodel.transformations import UVLReader, UVLWriter

from fm_solver.models.feature_model import FM
from fm_solver.utils import utils, constraints_utils
from fm_solver.transformations.refactorings import (
    RefactoringPseudoComplexConstraint,
    RefactoringStrictComplexConstraint
)


FM_OUTPUT_FILENAME_POSTFIX = '_simple'


def main(fm_filepath: str):
    # Get feature model name
    fm_name = '.'.join(os.path.basename(fm_filepath).split('.')[:-1])

    # Load the feature model
    feature_model = UVLReader(fm_filepath).transform()
    fm = FM.from_feature_model(feature_model)
    
    # Check if the feature model has any cross-tree constraints
    if not any(constraints_utils.is_complex_constraint(ctc) for ctc in fm.get_constraints()):
        print(f'Warning: The feature model has not any complex cross-tree constraints. The output FM is the same as the input.')

    # Refactor pseudo-complex constraints
    fm = utils.apply_refactoring(fm, RefactoringPseudoComplexConstraint)
    # Refactor strict-complex constraints
    fm = utils.apply_refactoring(fm, RefactoringStrictComplexConstraint)

    # Serializing the feature model    
    output_fm_filepath = f'{fm_name}{FM_OUTPUT_FILENAME_POSTFIX}.uvl'
    UVLWriter(path=output_fm_filepath, source_model=fm).transform()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert an FM in (.uvl) to an FM in (.uvl) with only simple constraints (requires and excludes).')
    parser.add_argument('-fm', '--featuremodel', dest='feature_model', type=str, required=True, help='Input feature model in UVL format.')
    args = parser.parse_args()

    main(args.feature_model)
    