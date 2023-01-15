import os
import argparse

from flamapy.metamodels.fm_metamodel.transformations import UVLReader

from flamapy.metamodels.pysat_metamodel.transformations import FmToPysat
from flamapy.metamodels.pysat_metamodel.operations import Glucose3ProductsNumber


def main(fm_filepath: str) -> None:
    # Get feature model name
    fm_name = '.'.join(os.path.basename(fm_filepath).split('.')[:-1])

    # Load the feature model
    fm = UVLReader(fm_filepath).transform()

    # Create the SAT model from the FM
    sat_model = FmToPysat(fm).transform()

    # Products numbers
    n_configs = Glucose3ProductsNumber().execute(sat_model).get_result()
    print(f'#Configs: {n_configs}')    


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyze an FM using the SAT Solver.')
    parser.add_argument('-fm', '--featuremodel', dest='feature_model', type=str, required=True, help='Input feature model in UVL format (.uvl).')
    args = parser.parse_args()

    main(args.feature_model)
    