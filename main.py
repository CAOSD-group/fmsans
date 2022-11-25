import argparse

from flamapy.metamodels.fm_metamodel.models import FeatureModel
from flamapy.metamodels.fm_metamodel.transformations import UVLReader, UVLWriter

from fm_solver.transformations import FMToFMSans
from fm_solver.transformations.refactorings import (
    RefactoringPseudoComplexConstraint,
    RefactoringStrictComplexConstraint,
    RefactoringRequiresConstraint,
    RefactoringExcludesConstraint
)

from fm_solver.operations import FMConfigurationsNumber
from fm_solver.utils import utils, fm_utils


def classic_approach(fm: FeatureModel) -> FeatureModel:
    fm = utils.apply_refactoring(fm, RefactoringPseudoComplexConstraint)
    fm = utils.apply_refactoring(fm, RefactoringStrictComplexConstraint)
    fm = utils.apply_refactoring(fm, RefactoringRequiresConstraint)
    fm = utils.apply_refactoring(fm, RefactoringExcludesConstraint)
    fm = fm_utils.remove_leaf_abstract_features(fm)
    return fm


def main(fm_filepath: str):
    # Load the feature model
    fm = UVLReader(fm_filepath).transform()
    
    # Transform the feature model to FMSans
    fm_sans = FMToFMSans(fm).transform()
    fm = fm_sans.get_feature_model()
    
    # Execute an analysis operation
    n_configurations = FMConfigurationsNumber().execute(fm).get_result()
    print(f'#Configurations: {n_configurations}')

    fm = fm_utils.to_unique_features(fm)
    UVLWriter(fm, fm_filepath + '_refactored.uvl').transform()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='FM Solver.')
    parser.add_argument('-fm', '--featuremodel', dest='feature_model', type=str, required=True, help='Input feature model in UVL format.')
    args = parser.parse_args()

    main(args.feature_model)
