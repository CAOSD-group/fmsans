import os
import argparse
import multiprocessing
import math

from flamapy.metamodels.fm_metamodel.transformations import UVLReader, UVLWriter

from fm_solver.models.feature_model import FM
from fm_solver.transformations import FMToFMSans
from fm_solver.utils import fm_utils

from fm_solver.operations import (
    FMConfigurationsNumber,
    FMFullAnalysis,
    FMCoreFeatures
)

from fm_solver.transformations import FMSansWriter


FM_OUTPUT_FILENAME_POSTFIX = '_fmsans'


def main(fm_filepath: str, n_cores: int):
    # Get feature model name
    fm_name = '.'.join(os.path.basename(fm_filepath).split('.')[:-1])

    # Load the feature model
    feature_model = UVLReader(fm_filepath).transform()
    
    # Transform the FM to the fmsans model
    fm = FM.from_feature_model(feature_model)
    fmsans_model = FMToFMSans(fm, n_cores=n_cores).transform()
    result = fmsans_model.get_analysis()
    n_configs = result[FMFullAnalysis.CONFIGURATIONS_NUMBER]
    print(f'Configs: {n_configs}')

    # Serializing the FMSans model
    output_fmsans_filepath = f'{fm_name}_{n_cores}.json'
    FMSansWriter(output_fmsans_filepath, fmsans_model).transform()

    fm_full = fmsans_model.get_feature_model()
    fm_full = fm_utils.to_unique_features(fm_full)
    output_fullfm_filepath = f'{fm_name}_full.uvl'
    UVLWriter(path=output_fullfm_filepath, source_model=fm).transform()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert an FM in (.uvl) with only simple constraints (requires and excludes) to an FMSans (.json).')
    parser.add_argument('-fm', '--featuremodel', dest='feature_model', type=str, required=True, help='Input feature model in UVL format.')
    parser.add_argument('-c', '--cores', dest='n_cores', type=int, required=False, default=multiprocessing.cpu_count(), help='Number of cores (processes) to execute (power of 2) (default = CPU count).')
    args = parser.parse_args()

    if args.n_cores <= 0 or not math.log(args.n_cores, 2).is_integer():
        print(f'The number of cores must be positive and power of 2.')
    else:
        main(args.feature_model, args.n_cores)
