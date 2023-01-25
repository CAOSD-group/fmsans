import argparse

from flamapy.metamodels.fm_metamodel.transformations import UVLReader

from fm_solver.models.feature_model import FM
from fm_solver.utils import fm_utils


def main(fm_filepath: str):
    # Load the feature model
    print(f'Reading FM model... {fm_filepath}')
    feature_model = UVLReader(fm_filepath).transform()

    # Get stats
    print(f'Bulding FM model...')
    fm = FM.from_feature_model(feature_model)
    print(f'Getting stats...')
    stats = fm_utils.fm_stats(fm)
    print(stats)
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Returns the stats of an FM in (.uvl).')
    parser.add_argument('-fm', '--featuremodel', dest='feature_model', type=str, required=True, help='Input feature model in UVL format.')
    args = parser.parse_args()

    main(args.feature_model)
