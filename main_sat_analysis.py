import os
import argparse
import time

from flamapy.metamodels.fm_metamodel.transformations import UVLReader

from flamapy.metamodels.pysat_metamodel.transformations import FmToPysat
from flamapy.metamodels.pysat_metamodel.operations import SATCoreFeatures


NS_TO_MS = 1e-6


def main(fm_filepath: str) -> None:
    # Get feature model name
    fm_name = '.'.join(os.path.basename(fm_filepath).split('.')[:-1])

    # Load the feature model
    fm = UVLReader(fm_filepath).transform()

    # Create the SAT model from the FM
    sat_model = FmToPysat(fm).transform()

    # Core features
    start_time = time.perf_counter_ns()
    core_features = SATCoreFeatures().execute(sat_model).get_result()
    end_time = time.perf_counter_ns()
    elapsed_time = (end_time - start_time) * NS_TO_MS
    print(f'Core features: {core_features}')
    print(f'Time: {elapsed_time} ms')    
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyze an FM using the SAT Solver.')
    parser.add_argument('-fm', '--featuremodel', dest='feature_model', type=str, required=True, help='Input feature model in UVL format (.uvl).')
    args = parser.parse_args()

    main(args.feature_model)
    