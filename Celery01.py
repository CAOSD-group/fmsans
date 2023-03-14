
import argparse

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


def main(fm_filepath: str, n_min: int, n_current: int, n_max: int, division_id: int,divisions_max: int,t_max: int):
    # Get feature model name

    # Load the feature model
   # print(f'Reading FM model... {fm_filepath}')
    feature_model = UVLReader(fm_filepath).transform()

    # Transform the FM to the fmsans model
    fm = FM.from_feature_model(feature_model)
    #print("NCores " + str(n_cores)+"NTask " + str(n_tasks)+"CurrentTask " + str(current_task))
    fmsans_model = CeleryFMToFMSans(fm,n_min,n_current,n_max,division_id,divisions_max,t_max).transform()
    #result = fmsans_model.get_analysis()
    #n_configs = result[FMFullAnalysis.CONFIGURATIONS_NUMBER]
    #print(f'Configs: {n_configs} ({utils.int_to_scientific_notation(n_configs)})')

    # Serializing the FMSans model
    # if (n_min>0):
    #    output_fmsans_filepath = f'{fm.root.name}_{n_cores}_{current_task}-{n_tasks}--{n_min}-{n_max}.json'
    # else:
    if (len(fmsans_model.transformations_ids) > 0):
        output_fmsans_filepath = f'R_1_{division_id}-{divisions_max}.json'
        FMSansWriter(output_fmsans_filepath, fmsans_model).transform()

    # fm_full = fmsans_model.get_feature_model()
    # fm_full = fm_utils.to_unique_features(fm_full)
    # output_fullfm_filepath = f'{fm.root.name}_full.uvl'
    # UVLWriter(path=output_fullfm_filepath, source_model=fm).transform()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Convert an FM in (.uvl) with only simple constraints (requires and excludes) to an FMSans (.json).')
    parser.add_argument('feature_model', type=str,
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
