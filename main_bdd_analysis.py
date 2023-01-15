import os
import argparse

from flamapy.metamodels.fm_metamodel.transformations import UVLReader

from flamapy.metamodels.bdd_metamodel.transformations import FmToBDD
from flamapy.metamodels.bdd_metamodel.operations import BDDProductsNumber, BDDProductDistribution


def main(fm_filepath: str) -> None:
    # Get feature model name
    fm_name = '.'.join(os.path.basename(fm_filepath).split('.')[:-1])

    # Load the feature model
    fm = UVLReader(fm_filepath).transform()

    # Create the BDD from the FM
    bdd_model = FmToBDD(fm).transform()

    # Products numbers
    n_configs = BDDProductsNumber().execute(bdd_model).get_result()
    print(f'#Configs: {n_configs}')    

    prod_dist = BDDProductDistribution().execute(bdd_model).get_result()
    print(f'#Configs (prod_dist): {sum(prod_dist)}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyze an FM using the BDD Solver.')
    parser.add_argument('-fm', '--featuremodel', dest='feature_model', type=str, required=True, help='Input feature model in UVL format (.uvl).')
    args = parser.parse_args()

    main(args.feature_model)
    