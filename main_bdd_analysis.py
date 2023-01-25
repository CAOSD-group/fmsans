import os
import argparse

from flamapy.metamodels.fm_metamodel.transformations import UVLReader, UVLWriter

from flamapy.metamodels.bdd_metamodel.transformations import FmToBDD
from flamapy.metamodels.bdd_metamodel.operations import (
    BDDProductsNumber, 
    BDDProductDistribution,
    BDDFeatureInclusionProbability
)

from fm_solver.models.feature_model import FM
from fm_solver.utils import utils


def main(fm_filepath: str) -> None:
    # Get feature model name
    fm_name = '.'.join(os.path.basename(fm_filepath).split('.')[:-1])

    # Load the feature model
    feature_model = UVLReader(fm_filepath).transform()
    fm = FM.from_feature_model(feature_model)

    # Create the BDD from the FM
    bdd_model = FmToBDD(fm).transform()

    # Products numbers
    n_configs = BDDProductsNumber().execute(bdd_model).get_result()
    print(f'#Configs: {n_configs} ({utils.int_to_scientific_notation(n_configs)})')

    # prod_dist = BDDProductDistribution().execute(bdd_model).get_result()
    # print(f'#Configs (prod_dist): {sum(prod_dist)}')

    # feat_prob = BDDFeatureInclusionProbability().execute(bdd_model).get_result()
    # for f, p in feat_prob.items():
    #     if p == 0:
    #         print(f)
    #         feature = fm.get_feature_by_name(f)
    #         if feature is not None:
    #             fm = fm_utils.deletion_feature(fm, f)

    # constraints = [ctc for ctc in fm.get_constraints()]
    # for ctc in fm.get_constraints():
    #     features = ctc.get_features()
    #     if any(fm.get_feature_by_name(f) is None for f in features):
    #         constraints.remove(ctc)
    
    # fm.ctcs = constraints

    # output_fm_filepath = f'{fm_name}_clean.uvl'
    # UVLWriter(path=output_fm_filepath, source_model=fm).transform()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyze an FM using the BDD Solver.')
    parser.add_argument('-fm', '--featuremodel', dest='feature_model', type=str, required=True, help='Input feature model in UVL format (.uvl).')
    args = parser.parse_args()

    main(args.feature_model)
    