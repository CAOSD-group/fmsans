import os
import argparse

from flamapy.metamodels.fm_metamodel.transformations import UVLReader, UVLWriter

from fm_solver.models.feature_model import FM
from fm_solver.utils import utils, constraints_utils
from fm_solver.transformations.refactorings import (
    RefactoringPseudoComplexConstraint,
    RefactoringStrictComplexConstraint,
    RefactoringExcludesConstraint
)
from fm_solver.utils import timer, fm_utils


FM_OUTPUT_FILENAME_POSTFIX = '_refactored'


def main(fm_filepath: str):
    # Get feature model name
    path, filename = os.path.split(fm_filepath)
    filename = ''.join(filename.split('.')[:-1])

    # Load the feature model
    print(f'Reading feature model from {fm_filepath}')
    feature_model = UVLReader(fm_filepath).transform()
    fm = FM.from_feature_model(feature_model)
    n_features = len(fm.get_features())
    n_ctcs = len(fm.get_constraints())
    for i, ctc in enumerate(fm.get_constraints()):
        print(f'CTC {i}: {ctc.ast.pretty_str()}')

    t0 = fm_utils.transform_tree(functions=[fm_utils.deletion_feature], fm=fm, features=['Normal'], copy_tree=True)
    t00 = fm_utils.transform_tree(functions=[fm_utils.deletion_feature], fm=t0, features=['Salami'], copy_tree=True)
    t01 = fm_utils.transform_tree(functions=[fm_utils.deletion_feature, fm_utils.commitment_feature], fm=t0, features=['Normal', 'Salami'], copy_tree=True)

    t1 = fm_utils.transform_tree(functions=[fm_utils.deletion_feature, fm_utils.commitment_feature], fm=fm, features=['CheesyCrust', 'Normal'], copy_tree=True)
    t10 = fm_utils.transform_tree(functions=[fm_utils.deletion_feature], fm=t1, features=['Salami'], copy_tree=True)
    t11 = fm_utils.transform_tree(functions=[fm_utils.deletion_feature, fm_utils.commitment_feature], fm=t1, features=['Normal', 'Salami'], copy_tree=True)
    
    print(t11)

    # Serializing the feature model
    output_fm_filepath = os.path.join(path, f'{filename}{"_t00"}.uvl')
    print(f'Serializing FM model in {output_fm_filepath} ...')
    UVLWriter(path=output_fm_filepath, source_model=t00).transform()

    output_fm_filepath = os.path.join(path, f'{filename}{"_t01"}.uvl')
    print(f'Serializing FM model in {output_fm_filepath} ...')
    UVLWriter(path=output_fm_filepath, source_model=t01).transform()

    output_fm_filepath = os.path.join(path, f'{filename}{"_t10"}.uvl')
    print(f'Serializing FM model in {output_fm_filepath} ...')
    UVLWriter(path=output_fm_filepath, source_model=t10).transform()

    output_fm_filepath = os.path.join(path, f'{filename}{"_t11"}.uvl')
    print(f'Serializing FM model in {output_fm_filepath} ...')
    UVLWriter(path=output_fm_filepath, source_model=t11).transform()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Pruebas.')
    parser.add_argument('-fm', '--featuremodel', dest='feature_model', type=str, required=True, help='Input feature model in UVL format.')
    args = parser.parse_args()

    if args.feature_model:
        main(args.feature_model)