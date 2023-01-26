import argparse
import statistics

from flamapy.metamodels.fm_metamodel.transformations import UVLReader
from flamapy.metamodels.bdd_metamodel.transformations import FmToBDD
from flamapy.metamodels.bdd_metamodel.operations import BDDProductsNumber


from fm_solver.models.feature_model import FM
from fm_solver.utils import fm_utils, utils
from fm_solver.transformations import FMSansReader
from fm_solver.operations import FMConfigurationsNumber


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

    bdd_model = FmToBDD(fm).transform()
    n_configs = BDDProductsNumber().execute(bdd_model).get_result()
    print(f'  #Configs:             {n_configs} ({utils.int_to_scientific_notation(n_configs)})')
    

def main_fmsans(fm_filepath: str):
    # Load the feature model
    print(f'Reading FM model... {fm_filepath}')
    fmsans_model = FMSansReader(fm_filepath).transform()

    # Get stats
    print(f'Bulding FM model...')
    fm = fmsans_model.get_feature_model()
    print(f'Getting stats...')
    stats = fm_utils.fm_stats(fm)
    print(stats)

    subtrees = fmsans_model.get_subtrees()
    features_subtrees = [len(st.get_features()) for st in subtrees]
    n_unique_features = len(fm_utils.get_unique_features(fm))
    n_subtrees = len(subtrees)  # 1 if fmsans_model.transformations_ids is None else len(fmsans_model.transformations_ids)
    n_configs = FMConfigurationsNumber().execute(fm).get_result()
    min_features_subtrees = min(features_subtrees)
    max_features_subtrees = max(features_subtrees)
    median_features_subtrees = round(statistics.median(features_subtrees), 2)
    mean_features_subtrees = round(statistics.mean(features_subtrees), 2)
    stdev_features_subtrees = round(statistics.stdev(features_subtrees), 2)
    print(f'  #Subtrees:            {n_subtrees}')
    print(f'    #Unique features:   {n_unique_features}')
    print(f'    #Min features:      {min_features_subtrees}')
    print(f'    #Max features:      {max_features_subtrees}')
    print(f'    #Median features:   {median_features_subtrees}')
    print(f'    #Mean features:     {mean_features_subtrees}')
    print(f'    #Stdev features:    {stdev_features_subtrees}')
    print(f'  #Configs:             {n_configs} ({utils.int_to_scientific_notation(n_configs)})')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Returns the stats of an FM.')
    input_model = parser.add_mutually_exclusive_group(required=True)
    input_model.add_argument('-fm', '--featuremodel', dest='feature_model', type=str, help='Input feature model in UVL format.')
    input_model.add_argument('-fmsans', dest='fmsans', type=str, help='Input feature model in FMSans (.json) format.')
    args = parser.parse_args()

    if args.feature_model:
        main(args.feature_model)
    elif args.fmsans:
        main_fmsans(args.fmsans) 
        pass
