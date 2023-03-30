
import argparse
import os
from typing import Dict, Tuple

from flamapy.metamodels.fm_metamodel.transformations import UVLReader, UVLWriter

from fm_solver.models.feature_model import FM
from fm_solver.transformations import CeleryFMToFMSans
from fm_solver.utils import utils

from fm_solver.operations import (
    FMConfigurationsNumber,
    FMFullAnalysis,
    FMCoreFeatures
)

from fm_solver.transformations import FMSansWriter
from fm_solver.models.utils.transformations_vector import get_min_max_ids_transformations_for_parallelization

FM_OUTPUT_FILENAME_POSTFIX = '_fmsans'


get_min_max_ids_transformations_for_parallelization


def main(fm_filepath: str, n_min: int, n_current: int, n_max: int, division_id: int,divisions_max: int,t_max: int)  -> Tuple[Dict[str, int], int, int, int] :
    # Get feature model name

    # Load the feature model
   # print(f'Reading FM model... {fm_filepath}')
    feature_model = UVLReader(fm_filepath).transform()

    # Transform the FM to the fmsans model
    fm = FM.from_feature_model(feature_model)
    #print("main nTask " + str(divisions_max) + " current_task " + str(division_id) + " min_id " + str(n_min) + " current_id " + str(n_current) + " max_id " + str(n_max) + " max_time " + str(t_max) )
   
    #It returns a list with a [valid_transformed_numbers_trees,n_min,n_current,n_max]
    dict, n_min, n_current, n_max = CeleryFMToFMSans(fm,n_min,n_current,n_max,division_id,divisions_max,t_max).transform()

    return dict, n_min, n_current, n_max
    


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Convert an FM in (.uvl) with only simple constraints (requires and excludes) to an FMSans (.json).')
    parser.add_argument('feature_model', type=bytes,
                        help='Input feature model in UVL format.')
    parser.add_argument('n_min', type=int,  default="",
                        help='Minimun division')
    parser.add_argument('n_current', type=int,
                        default="", help='Current progress in a divisions.')
    parser.add_argument('division_id', type=int,
                        default="", help='Current id of file with divisions.')
    parser.add_argument('divisions_max', type=int,  default="",
                        help='Minimun division')
    parser.add_argument('t_max', type=int, default=-1, help='Number max.')
    args = parser.parse_args()

    main(args.feature_model, args.n_min, args.n_current,args.n_max,args.division_id,args.divisions_max,args.t_max)
