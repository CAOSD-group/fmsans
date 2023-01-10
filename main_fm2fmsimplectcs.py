import os
import argparse

from flamapy.metamodels.fm_metamodel.transformations import UVLReader, UVLWriter

from fm_solver.utils import utils, fm_utils, constraints_utils, logging_utils, timer, sizer
from fm_solver.transformations.refactorings import (
    RefactoringPseudoComplexConstraint,
    RefactoringStrictComplexConstraint
)


FM_OUTPUT_FILENAME_POSTFIX = '_simple'


def main(fm_filepath: str):
    # Get feature model name
    logging_utils.FM_LOGGER.info(f'Input model: {fm_filepath}')
    fm_name = '.'.join(os.path.basename(fm_filepath).split('.')[:-1])
    logging_utils.FM_LOGGER.info(f'FM name: {fm_name}')

    # Load the feature model
    logging_utils.LOGGER.info(f"Reading FM '{fm_filepath}' model...")
    with timer.Timer(logger=logging_utils.LOGGER.info, message="FM loading."):
        fm = UVLReader(fm_filepath).transform()
    sizer.getsizeof(fm, logging_utils.LOGGER.info, message="Input FM.")
    logging_utils.FM_LOGGER.info('Input FM:')
    logging_utils.FM_LOGGER.info(fm_utils.fm_stats(fm))
    
    # Check if the feature model has any cross-tree constraints
    logging_utils.LOGGER.debug(f'The input FM has {len(fm.get_features())} features, {len(fm.get_relations())} relations, and {len(fm.get_constraints())} constraints.')
    if not fm.get_constraints():
        logging_utils.LOGGER.debug(f'The FM has not constraints.')
        print(f'The feature model has not any cross-tree constraints. Nothing to do.')
        return

    # Refactor pseudo-complex constraints
    with timer.Timer(logger=logging_utils.LOGGER.debug, message="Refactoring pseudo-complex constraints."):
        fm = utils.apply_refactoring(fm, RefactoringPseudoComplexConstraint)
    # Refactor strict-complex constraints
    with timer.Timer(logger=logging_utils.LOGGER.debug, message="Refactoring strict-complex constraints."):
        fm = utils.apply_refactoring(fm, RefactoringStrictComplexConstraint)
    
    sizer.getsizeof(fm, logging_utils.LOGGER.info, message="Output FM.")
    logging_utils.LOGGER.debug(f'The simple FM has {len(fm.get_features())} features, {len(fm.get_relations())} relations, and {len(fm.get_constraints())} basic constraints ({sum(constraints_utils.is_requires_constraint(ctc) for ctc in fm.get_constraints())} requires, {sum(constraints_utils.is_excludes_constraint(ctc) for ctc in fm.get_constraints())} excludes) after complex constraints refactorings.')
    logging_utils.FM_LOGGER.info('Output FM:')
    logging_utils.FM_LOGGER.info(fm_utils.fm_stats(fm))

    # Serializing the feature model    
    logging_utils.LOGGER.info(f"Serializing FM...")
    output_fm_filepath = f'{fm_name}{FM_OUTPUT_FILENAME_POSTFIX}.uvl'
    with timer.Timer(logger=logging_utils.LOGGER.info, message="FM serialization."):
        UVLWriter(path=output_fm_filepath, source_model=fm).transform()
    logging_utils.LOGGER.info(f"FM saved at {output_fm_filepath}.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert an FM in (.uvl) to an FM in (.uvl) with only simple constraints (requires and excludes).')
    parser.add_argument('-fm', '--featuremodel', dest='feature_model', type=str, required=True, help='Input feature model in UVL format.')
    args = parser.parse_args()

    main(args.feature_model)
    