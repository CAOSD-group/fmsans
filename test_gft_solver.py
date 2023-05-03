import os
import sys
import argparse

from flamapy.metamodels.fm_metamodel.transformations import UVLReader

from fm_solver.operations import (
    FMConfigurationsNumber, 
    FMCoreFeatures, 
    FMDeadFeaturesGFT,
    FMValid
)


def main(fm_filepath: str) -> None:
    # Get feature model name
    path, filename = os.path.split(fm_filepath)
    filename = '.'.join(filename.split('.')[:-1])

    print(f'  Reading FM model (.uvl)...')
    fm = UVLReader(fm_filepath).transform()

    print(f'Analyzing model...')

    print(f'    > Valid operation...')
    valid = FMValid().execute(fm).get_result()
    print(f'Valid? {valid}')

    print(f'    > Products number...')
    n_configs = FMConfigurationsNumber().execute(fm).get_result()
    print(f'#Products: {n_configs}')

    print(f'    > Core features...')
    core_features = FMCoreFeatures().execute(fm).get_result()
    print(f'Core features: {len(core_features)} {[f for f in core_features]}')

    print(f'    > Dead features...')
    dead_features = FMDeadFeaturesGFT().execute(fm).get_result()
    print(f'Dead features: {len(dead_features)} {[f for f in dead_features]}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyze an FM using the GFT solver.')
    parser.add_argument('-fm', '--featuremodel', dest='feature_model', required=True, type=str, help='Input feature model in UVL (.uvl) format.')
    args = parser.parse_args()

    if args.feature_model:    
        if not args.feature_model.endswith('.uvl'):
            sys.exit(f'Error, incorrect file format for {args.feature_model}. It should be a UVL (.uvl) model.')

        main(args.feature_model)
            

