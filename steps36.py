import os
import sys
import math
import argparse
import multiprocessing

from flamapy.metamodels.fm_metamodel.transformations import UVLWriter

from fm_solver.transformations import FMSansReader
from fm_solver.utils import timer
from fm_solver.models.feature_model import FM


FM_OUTPUT_FILENAME_POSTFIX = '_gft'
TIME = 'TIME'


def main(fm_filepath: str, n_cores: int) -> None:
    # Get feature model name
    path, filename = os.path.split(fm_filepath)
    filename = '.'.join(filename.split('.')[:-1])

    # Load the feature model (FMSans)
    print(f'Reading FMSans model... {fm_filepath}')
    fmsans_model = FMSansReader(fm_filepath).transform()

    # Perform full analysis of FMSans
    print(f'Building the Generalized Feature Tree from {len(fmsans_model.transformations_ids)} subtrees...')
    with timer.Timer(name=TIME, logger=None):
        fm = fmsans_model.get_feature_model(n_cores)

    total_time = timer.Timer.timers[TIME]
    total_time = round(total_time, 4)
    print(f'Time (building GFT): {total_time} s.')

    print(f'Bulding FM model...')
    fm = FM.from_feature_model(fm)
    #fm = fm_utils.to_unique_features(fm)

    # Serializing the feature model
    output_fm_filepath = os.path.join(path, f'{filename}{FM_OUTPUT_FILENAME_POSTFIX}.uvl')
    print(f'Serializing FM model in {output_fm_filepath} ...')
    UVLWriter(path=output_fm_filepath, source_model=fm).transform()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate a generalized feature tree (GFT) in UVL format (.uvl) from the FMSans model (.json).')
    parser.add_argument('-fm', '--featuremodel', dest='feature_model', type=str, required=True, help='Input feature model in FMSans format (.json).')
    parser.add_argument('-c', '--cores', dest='n_cores', type=int, required=False, default=multiprocessing.cpu_count(), help='Number of cores (processes) to execute (power of 2) (default = CPU count).')
    args = parser.parse_args()

    if args.n_cores <= 0 or not math.log(args.n_cores, 2).is_integer():
        if args.n_cores == multiprocessing.cpu_count():
            sys.exit(f'The number of cores of this computer is not a power of 2. Please set the -c parameter to a power of 2.')
        else:
            sys.exit(f'The number of cores must be positive and power of 2.')
    if not args.feature_model.endswith('.json'):
        sys.exit(f'Error, incorrect file format for {args.feature_model}. It should be a FMSans model (.json).')

    main(args.feature_model, args.n_cores)
