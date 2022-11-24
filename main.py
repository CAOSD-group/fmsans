import argparse

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


def main(fm_filepath: str):
    # Load the feature model
    fm = UVLReader(fm_filepath).transform()
    # Transform the feature model to FMSans
    #fm_sans = FMToFMSans(source_model=fm).transform()

    fm = utils.apply_refactoring(fm, RefactoringPseudoComplexConstraint)
    UVLWriter(fm, fm_filepath + '_refactored1.uvl').transform()
    fm = utils.apply_refactoring(fm, RefactoringStrictComplexConstraint)
    UVLWriter(fm, fm_filepath + '_refactored2.uvl').transform()
    fm = utils.apply_refactoring(fm, RefactoringRequiresConstraint)
    UVLWriter(fm, fm_filepath + '_refactored3.uvl').transform()
    fm = utils.apply_refactoring(fm, RefactoringExcludesConstraint)
    fm = fm_utils.remove_leaf_abstract_features(fm)


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
