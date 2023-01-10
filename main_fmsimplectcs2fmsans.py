import os
import argparse

from flamapy.metamodels.fm_metamodel.transformations import UVLReader

from fm_solver.models import FMSans
from fm_solver.models.fm_sans import (
    fmsans_stats, 
    get_transformations_vector, 
    get_valid_transformations_ids, 
    get_basic_constraints_order
)

from fm_solver.transformations import FMSansWriter
from fm_solver.utils import fm_utils, constraints_utils, logging_utils, timer, sizer


FM_OUTPUT_FILENAME_POSTFIX = '_fmsans'


def main(fm_filepath: str):
    # Get feature model name
    logging_utils.FM_LOGGER.info(f'Input model: {fm_filepath}')
    fm_name = '.'.join(os.path.basename(fm_filepath).split('.')[:-1])
    logging_utils.FM_LOGGER.info(f'FM name: {fm_name}')

    # Load the feature model
    logging_utils.LOGGER.info(f"Reading FM '{fm_filepath}' model...")
    with timer.Timer(logger=logging_utils.LOGGER.info, message="FM loading."):
        fm = UVLReader(fm_filepath).transform()
    sizer.getsizeof(fm, logging_utils.LOGGER.info, message="FM.")
    logging_utils.FM_LOGGER.info('Input FM:')
    logging_utils.FM_LOGGER.info(fm_utils.fm_stats(fm))
    
    # Check if the feature model has only basic cross-tree constraints (requires and excludes)
    logging_utils.LOGGER.debug(f'The input FM has {len(fm.get_features())} features, {len(fm.get_relations())} relations, and {len(fm.get_constraints())} constraints.')
    if any(constraints_utils.is_complex_constraint(ctc) for ctc in fm.get_constraints()):
        logging_utils.LOGGER.debug(f'The FM has complex constraints. Please use before the "main_fm2fmsimplectcs.py" script to refactor them.')
        print(f'The feature model has complex constraints. Please use before the "main_fm2fmsimplectcs.py" script to refactor them.')
        return

    # Split the feature model into two
    logging_utils.LOGGER.debug(f'Spliting FM tree...')
    with timer.Timer(logger=logging_utils.LOGGER.debug, message="Split FM tree."):
        subtree_with_constraints_implications, subtree_without_constraints_implications = fm_utils.get_subtrees_constraints_implications(fm)
    logging_utils.LOGGER.debug(f'Subtree with no CTCs implications: {0 if subtree_without_constraints_implications is None else len(subtree_without_constraints_implications.get_features())} features.')
    logging_utils.LOGGER.debug(f'Subtree with CTCs implications: {0 if subtree_with_constraints_implications is None else len(subtree_with_constraints_implications.get_features())} features.')

    # Get constraints order
    logging_utils.LOGGER.debug(f'Getting basic constraints order...')
    with timer.Timer(logger=logging_utils.LOGGER.debug, message="Constraints order."):
        constraints_order = get_basic_constraints_order(fm)
    
    # Get transformations vector
    logging_utils.LOGGER.debug(f'Getting transformations vector...')
    with timer.Timer(logger=logging_utils.LOGGER.debug, message="Transformations vector."):
        transformations_vector = get_transformations_vector(constraints_order)
    logging_utils.LOGGER.debug(f'Transformations vector length: {len(transformations_vector)} constraints.')

    # Get valid transformations ids.
    logging_utils.LOGGER.debug(f'Getting valid transformations IDs...')
    with timer.Timer(logger=logging_utils.LOGGER.debug, message="Valid transformations IDs."):
        valid_transformed_numbers_trees = get_valid_transformations_ids(subtree_with_constraints_implications, transformations_vector)
    logging_utils.LOGGER.debug(f'#Valid subtrees: {len(valid_transformed_numbers_trees)} subtrees from {2**len(transformations_vector)}.')

    # Get FMSans instance
    fm_sans_model = FMSans(subtree_with_constraints_implications=subtree_with_constraints_implications, 
                       subtree_without_constraints_implications=subtree_without_constraints_implications,
                       transformations_vector=transformations_vector,
                       transformations_ids=valid_transformed_numbers_trees)

    sizer.getsizeof(fm_sans_model, logging_utils.LOGGER.info, message="FMSans.")
    logging_utils.FM_LOGGER.info(fmsans_stats(fm_sans_model))
    
    # Serializing the FMSans model
    logging_utils.LOGGER.info(f"Serializing FMSans...")
    output_fmsans_filepath = f'{fm_name}.json'
    with timer.Timer(logger=logging_utils.LOGGER.info, message="FMSans serialization."):
        FMSansWriter(output_fmsans_filepath, fm_sans_model).transform()
    logging_utils.LOGGER.info(f"FMSans saved at {output_fmsans_filepath}.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert an FM in (.uvl) with only simple constraints (requires and excludes) to an FMSans (.json).')
    parser.add_argument('-fm', '--featuremodel', dest='feature_model', type=str, required=True, help='Input feature model in UVL format.')
    args = parser.parse_args()

    main(args.feature_model)
