
import argparse
import multiprocessing

import csv
import decimal

from flamapy.metamodels.fm_metamodel.transformations import UVLReader, UVLWriter

from fm_solver.models.feature_model import FM
from fm_solver.transformations import FMToFMSans
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


def main(fm_filepath: str, n_cores: int, n_tasks: int = 1, current_task: int = 1,n_min: int = -1,n_max: int = -1,t_min:int=-1,t_max:int=-1):
    # Get feature model name

    # Load the feature model
    print(f'Reading FM model... {fm_filepath}')
    feature_model = UVLReader(fm_filepath).transform()
    
    # Transform the FM to the fmsans model
    fm = FM.from_feature_model(feature_model)
    fmsans_model = FMToFMSans(fm, n_cores=n_cores, n_tasks=n_tasks, current_task=current_task,n_min=n_min,n_max=n_max,min_time=t_min,max_time=t_max).transform()
    #result = fmsans_model.get_analysis()
    #n_configs = result[FMFullAnalysis.CONFIGURATIONS_NUMBER]
    #print(f'Configs: {n_configs} ({utils.int_to_scientific_notation(n_configs)})')

    # Serializing the FMSans model
    #if (n_min>0):
    #    output_fmsans_filepath = f'{fm.root.name}_{n_cores}_{current_task}-{n_tasks}--{n_min}-{n_max}.json'
    #else:   
    output_fmsans_filepath = f'R_{n_cores}_{current_task}-{n_tasks}.json'
    FMSansWriter(output_fmsans_filepath, fmsans_model).transform()

    # fm_full = fmsans_model.get_feature_model()
    # fm_full = fm_utils.to_unique_features(fm_full)
    # output_fullfm_filepath = f'{fm.root.name}_full.uvl'
    # UVLWriter(path=output_fullfm_filepath, source_model=fm).transform()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert an FM in (.uvl) with only simple constraints (requires and excludes) to an FMSans (.json).')
    parser.add_argument('feature_model', type=str, help='Input feature model in UVL format.')
    parser.add_argument('n_cores', type=int, default=multiprocessing.cpu_count(), help='Number of cores (processes) to execute (power of 2) (default = CPU count).')
    parser.add_argument('n_tasks', type=int,  default=-1, help='Number of tasks.')
    parser.add_argument('current_task', type=int, default=-1, help='Current task.')
    parser.add_argument('fileDivision', type=str,  default="", help='File with divisions.')
    parser.add_argument('t_min', type=int,  default=-1, help='Number min.')
    parser.add_argument('t_max', type=int, default=-1, help='Number max.')
    args = parser.parse_args()

    #Explore by divisions if a file is provided.
    n_min = -1
    n_max = -1
    if (len(args.fileDivision)>3):
        with open(args.fileDivision, newline='') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=';')
            for row in spamreader:
                if (int(row[0])==args.current_task):
                    n_min=int(row[1])
                    n_max=int(row[2])
                    break


    main(args.feature_model, args.n_cores, args.n_tasks, args.current_task, n_min,n_max,args.t_min,args.t_max)
