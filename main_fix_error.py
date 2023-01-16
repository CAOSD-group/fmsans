import copy
import os
import argparse
import multiprocessing
import math

from flamapy.metamodels.fm_metamodel.models import FeatureModel
from flamapy.metamodels.fm_metamodel.transformations import UVLReader

from flamapy.metamodels.bdd_metamodel.transformations import FmToBDD
from flamapy.metamodels.bdd_metamodel.operations import BDDProductsNumber, BDDProductDistribution

from fm_solver.transformations import FMToFMSans
from fm_solver.models.feature_model import FM
from fm_solver.operations import (
    FMFullAnalysis,
)


FM_OUTPUT_FILENAME_POSTFIX = '_fmsans'


def fmsans_test(fm: FM) -> int:
    fm_sans_model = FMToFMSans(fm, 8).transform()
    result = fm_sans_model.get_analysis()
    return result[FMFullAnalysis.CONFIGURATIONS_NUMBER]


def bdd_test(fm: FeatureModel) -> int:
    # Create the BDD from the FM
    bdd_model = FmToBDD(fm).transform()

    # Products numbers
    n_configs = BDDProductsNumber().execute(bdd_model).get_result()
    print(f'#Configs: {n_configs}')    

    prod_dist = BDDProductDistribution().execute(bdd_model).get_result()
    print(f'#Configs (prod_dist): {sum(prod_dist)}')

    return n_configs
    

def main(fm_filepath: str, n_cores: int) -> int:
    # Get feature model name
    fm_name = '.'.join(os.path.basename(fm_filepath).split('.')[:-1])

    # Load the feature model
    feature_model = UVLReader(fm_filepath).transform()

    #constraints = reversed(feature_model.get_constraints())
    constraints = feature_model.get_constraints()
    #constraints = [constraints[3]]
    constraints_incremental = []
    errors = {}
    print(f'Constraints: {len(constraints)}')
    for i, ctc in enumerate(constraints):
        constraints_incremental.append(ctc)
        feature_model = FeatureModel(copy.deepcopy(feature_model.root), constraints_incremental)
        fm = FM.from_feature_model(feature_model)
        
        print(f'{i} -> {ctc.ast.pretty_str()}')
        n_configs1 = fmsans_test(fm)
        n_configs2 = bdd_test(feature_model)
        if n_configs1 != n_configs2:
            #output_fullfm_filepath = f'{fm_name}_error_{i}.uvl'
            #fm_output = fm_sans_model.get_feature_model()
            #fm_output = fm_utils.to_unique_features(fm_output)
            #UVLWriter(path=output_fullfm_filepath, source_model=fm_output).transform()
            constraints_incremental.remove(ctc)
            errors[i] = ctc
            raise Exception
        print('------------------------------')

    for i, c in errors.items():
        print(f'{i}: {c.ast.pretty_str()}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert an FM in (.uvl) with only simple constraints (requires and excludes) to an FMSans (.json).')
    parser.add_argument('-fm', '--featuremodel', dest='feature_model', type=str, required=True, help='Input feature model in UVL format.')
    parser.add_argument('-c', '--cores', dest='n_cores', type=int, required=False, default=multiprocessing.cpu_count(), help='Number of cores (processes) to execute (power of 2).')
    args = parser.parse_args()

    if args.n_cores <= 0 or not math.log(args.n_cores, 2).is_integer():
        print(f'The number of cores must be positive and power of 2.')
    else:
        main(args.feature_model, args.n_cores)
