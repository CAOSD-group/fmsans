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


def get_fm_filepath_models(dir: str) -> list[str]:
    """Get all models from the given directory."""
    models = []
    for root, dirs, files in os.walk(dir):
        for file in files:
            filepath = os.path.join(root, file)
            models.append(filepath)
    return models


def main(dir: str):
    models_filepaths = get_fm_filepath_models(dir)

    for i, fm_filepath in enumerate(models_filepaths, 1):
        try:
            if fm_filepath.endswith('.uvl'):
                # Load the feature model
                feature_model = UVLReader(fm_filepath).transform()

                # Get stats
                fm = FM.from_feature_model(feature_model)
                n_ctcs = len(fm.get_constraints())
                n_basic_ctcs = sum(constraints_utils.is_simple_constraint(ctc) for ctc in fm.get_constraints())
                print(f'FM {i}: {fm_filepath}. #Constraints: {n_ctcs} ({n_basic_ctcs} basics)')
                if n_ctcs > 10 and n_ctcs < 800:
                    new_fm, output_filepath = transform_to_basic(fm_filepath)
                    n_ctcs_new = len(new_fm.get_constraints())
                    with open('models_to_tests.csv', 'a') as csv_file:
                        str_content = f'{output_filepath},{n_ctcs_new},{2**n_ctcs_new}{os.linesep}'
                        csv_file.write(str_content)
        except Exception as e:
            print(e)
            print(f'Error in model: {fm_filepath}')


def transform_to_basic(fm_filepath: str) -> tuple[FM, str]:
    # Get feature model name
    fm_name = '.'.join(os.path.basename(fm_filepath).split('.')[:-1])

    # Load the feature model
    print(f'Reading FM model... {fm_filepath}')
    feature_model = UVLReader(fm_filepath).transform()
    fm = FM.from_feature_model(feature_model)
    
    # Check if the feature model has any cross-tree constraints
    if not any(constraints_utils.is_complex_constraint(ctc) for ctc in fm.get_constraints()):
        print(f'Warning: The feature model has not any complex cross-tree constraints. The output FM is the same as the input.')

    # Refactor pseudo-complex constraints
    print(f'Refactoring pseudo-complex constraints...')
    fm = utils.apply_refactoring(fm, RefactoringPseudoComplexConstraint)
    # Refactor strict-complex constraints
    print(f'Refactoring strict-complex constraints...')
    fm = utils.apply_refactoring(fm, RefactoringStrictComplexConstraint)

    # Serializing the feature model    
    output_fm_filepath = f'fm_models{os.path.sep}simples{os.path.sep}{fm_name}{FM_OUTPUT_FILENAME_POSTFIX}.uvl'
    UVLWriter(path=output_fm_filepath, source_model=fm).transform()

    return (fm, output_fm_filepath)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert all FM in the given folder in (.uvl) to an FM in (.uvl) with only simple constraints (requires and excludes).')
    parser.add_argument(dest='dir', type=str, help='Folder with the models.')
    args = parser.parse_args()

    main(args.dir)
    