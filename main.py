import argparse

from flamapy.metamodels.fm_metamodel.transformations import UVLReader


def main(fm_filepath: str):
    # Load the feature model
    fm = UVLReader(fm_filepath).transform()
    print(fm)

    # Transform the feature model to FMSans
    pass

    # Execute an analysis operation
    pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='FM Solver.')
    parser.add_argument('-fm', '--featuremodel', dest='feature_model', type=str, required=True, help='Input feature model in UVL format.')
    args = parser.parse_args()

    main(args.feature_model)
