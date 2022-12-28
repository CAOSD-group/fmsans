import os
import argparse

from flamapy.metamodels.fm_metamodel.transformations import UVLReader, UVLWriter

from fm_solver.transformations import FMToFMSans, FMSansWriter
from fm_solver.utils import fm_utils, logging_utils, timer, sizer
from fm_solver.models import fm_sans as fm_sans_utils


def main(fm_filepath: str, store_full_fm: bool = False, unique_features: bool = False):
    # Get feature model name
    logging_utils.FM_LOGGER.info(f'Input model: {fm_filepath}')
    fm_name = '.'.join(os.path.basename(fm_filepath).split('.')[:-1])
    logging_utils.FM_LOGGER.info(f'FM name: {fm_name}')

    # Load the feature model
    logging_utils.LOGGER.info(f"Reading FM '{fm_filepath}' model...")
    with timer.Timer(logger=logging_utils.LOGGER.info, message="FM loading."):
        fm = UVLReader(fm_filepath).transform()
    sizer.getsizeof(fm, logging_utils.LOGGER.info, message="FM.")
    logging_utils.FM_LOGGER.info(fm_sans_utils.fm_stats(fm))
    
    # Transform the feature model to FMSans
    logging_utils.LOGGER.info(f"Transforming FM to FMSans...")
    with timer.Timer(logger=logging_utils.LOGGER.info, message="FM to FMSans transformation."):
        fm_sans = FMToFMSans(fm).transform()
    sizer.getsizeof(fm_sans, logging_utils.LOGGER.info, message="FMSans.")
    logging_utils.FM_LOGGER.info(fm_sans_utils.fmsans_stats(fm_sans))
    
    logging_utils.LOGGER.info(f"Serializing FMSans...")
    output_fmsans_filepath = f'{fm_name}.json'
    with timer.Timer(logger=logging_utils.LOGGER.info, message="FMSans serialization."):
        FMSansWriter(output_fmsans_filepath, fm_sans).transform()
    logging_utils.LOGGER.info(f"FMSans saved at {output_fmsans_filepath}.")

    if store_full_fm:
        # Get full FM
        logging_utils.LOGGER.info(f"Getting full feature model...")
        with timer.Timer(logger=logging_utils.LOGGER.info, message="Applying IDs transformations."):
            fm = fm_sans.get_feature_model()
            sizer.getsizeof(fm, logging_utils.LOGGER.info, message="Full FM.")
        logging_utils.FM_LOGGER.info(fm_sans_utils.fm_stats(fm))

        # Convert non-unique features to unique features
        if unique_features:
            logging_utils.LOGGER.info(f"Converting non-unique features to unique features...")
            with timer.Timer(logger=logging_utils.LOGGER.info, message="To unique features."):
                fm = fm_utils.to_unique_features(fm)
                sizer.getsizeof(fm, logging_utils.LOGGER.info, message="FM with unique features.")
            logging_utils.FM_LOGGER.info(fm_sans_utils.fm_stats(fm))

        # Serializing full FM
        logging_utils.LOGGER.info(f"Serializing full FM...")
        output_fullfm_filepath = f'{fm_name}_full.uvl'
        with timer.Timer(logger=logging_utils.LOGGER.info, message="Full FM serialization."):
            UVLWriter(path=output_fullfm_filepath, source_model=fm).transform()
        logging_utils.LOGGER.info(f"Full FM saved at {output_fullfm_filepath}.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert an FM to an FMSans (.json).')
    parser.add_argument('-fm', '--featuremodel', dest='feature_model', type=str, required=True, help='Input feature model in UVL format.')
    parser.add_argument('-o', '--output', dest='output', action='store_true', default=False, required=False, help='Save also the output full feature model without constraints in UVL format.')
    parser.add_argument('-u', '--unique', dest='unique_features', action='store_true', default=False, required=False, help="The full feature model is stored with unique features' names (only if -o option is provided).")
    args = parser.parse_args()

    main(args.feature_model, args.output, args.unique_features)
    