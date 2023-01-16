import pickle
import os
import argparse
import multiprocessing
import math
from multiprocessing import Process, Queue

from flamapy.metamodels.fm_metamodel.transformations import UVLReader, UVLWriter

from fm_solver.models.feature_model import FM
from fm_solver.models import FMSans
from fm_solver.models.fm_sans import (
    get_transformations_vector, 
    get_valid_transformations_ids, 
    get_basic_constraints_order,
    get_min_max_ids_transformations_for_parallelization
)
from fm_solver.operations import (
    FMConfigurationsNumber,
    FMFullAnalysis,
    FMCoreFeatures
)


from fm_solver.transformations import FMSansWriter, FMSansReader
from fm_solver.utils import fm_utils, constraints_utils


FM_OUTPUT_FILENAME_POSTFIX = '_fmsans'


def main(fm_filepath: str, n_cores: int):
    # Get feature model name
    fm_name = '.'.join(os.path.basename(fm_filepath).split('.')[:-1])

    # Load the feature model
    feature_model = UVLReader(fm_filepath).transform()
    fm = FM.from_feature_model(feature_model)
    
    # Check if the feature model has only basic cross-tree constraints (requires and excludes)
    if any(constraints_utils.is_complex_constraint(ctc) for ctc in fm.get_constraints()):
        print(f'The feature model has complex constraints. Please use before the "main_fm2fmsimplectcs.py" script to refactor them.')
        return None

    if fm.get_constraints():  # The feature model has constraints.
        # Split the feature model into two
        subtree_with_constraints_implications, subtree_without_constraints_implications = fm_utils.get_subtrees_constraints_implications(fm)
        #subtree_with_constraints_implications, subtree_without_constraints_implications = fm, None
        
        # Get constraints order
        constraints_order = get_basic_constraints_order(fm)

        # Get transformations vector
        transformations_vector = get_transformations_vector(constraints_order)

        # Get valid transformations ids.
        ### PARALLEL CODE
        valid_transformed_numbers_trees = {}
        queue = Queue()
        processes = []
        n_bits = len(constraints_order[0])
        cpu_count = n_cores
        n_processes = cpu_count if n_bits > cpu_count else 1
        pick_tree = pickle.dumps(subtree_with_constraints_implications, protocol=pickle.HIGHEST_PROTOCOL)
        for process_i in range(n_processes):
            min_id, max_id = get_min_max_ids_transformations_for_parallelization(n_bits, n_processes, process_i)
            p = Process(target=get_valid_transformations_ids, args=(pick_tree, transformations_vector, min_id, max_id, queue))
            p.start()
            processes.append(p)

        for p in processes:
            valid_ids = queue.get()
            valid_transformed_numbers_trees.update(valid_ids)
        ### End of parallel code.

        # Get FMSans instance
        fm_sans_model = FMSans(subtree_with_constraints_implications=subtree_with_constraints_implications, 
                        subtree_without_constraints_implications=subtree_without_constraints_implications,
                        transformations_vector=transformations_vector,
                        transformations_ids=valid_transformed_numbers_trees)
    else:  # The feature model has not any constraint.
        fm_sans_model = FMSans(None, fm, [], {})

    # Serializing the FMSans model
    output_fmsans_filepath = f'{fm_name}_{n_processes}.json'
    FMSansWriter(output_fmsans_filepath, fm_sans_model).transform()

    # fm_full = fm_sans_model.get_feature_model()
    # fm_full = fm_utils.to_unique_features(fm_full)
    # output_fullfm_filepath = f'{fm_name}_full.uvl'
    # UVLWriter(path=output_fullfm_filepath, source_model=fm).transform()

    #print(FM(feature_model.root) == fm_sans_model.subtree_with_constraints_implications)

    #fm_sans2 = FMSansReader(output_fmsans_filepath).transform()
    # print(fm_sans2.subtree_with_constraints_implications == fm_sans_model.subtree_with_constraints_implications)
    # print(fm_sans2.subtree_without_constraints_implications == fm_sans_model.subtree_without_constraints_implications)
    # print(fm_sans2.transformations_ids == fm_sans_model.transformations_ids)
    # print(fm_sans2.transformations_vector == fm_sans_model.transformations_vector)
    # print(fm_sans2 == fm_sans_model)

    result = fm_sans_model.get_analysis()
    print(f'Result from paralelization analysis: ')
    print(f'#Configurations: {result[FMFullAnalysis.CONFIGURATIONS_NUMBER]}')
    print(f'Core features: {len(result[FMFullAnalysis.CORE_FEATURES])}, {[f.name for f in result[FMFullAnalysis.CORE_FEATURES]]}')

    fm = fm_sans_model.get_feature_model()
    print(f'Result from full composed feature model: ')
    n_configurations = FMConfigurationsNumber().execute(fm).get_result()
    print(f'#Configurations: {n_configurations}')

    core_features = FMCoreFeatures().execute(fm).get_result()
    print(f'Core features: {len(core_features)}, {[f.name for f in core_features]}')



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert an FM in (.uvl) with only simple constraints (requires and excludes) to an FMSans (.json).')
    parser.add_argument('-fm', '--featuremodel', dest='feature_model', type=str, required=True, help='Input feature model in UVL format.')
    parser.add_argument('-c', '--cores', dest='n_cores', type=int, required=False, default=multiprocessing.cpu_count(), help='Number of cores (processes) to execute (power of 2).')
    args = parser.parse_args()

    if args.n_cores <= 0 or not math.log(args.n_cores, 2).is_integer():
        print(f'The number of cores must be positive and power of 2.')
    else:
        main(args.feature_model, args.n_cores)
