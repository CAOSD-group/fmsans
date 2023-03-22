import os
import sys
import math
import argparse
import statistics
import multiprocessing

from flamapy.metamodels.fm_metamodel.transformations import UVLReader
from flamapy.metamodels.bdd_metamodel.transformations import FmToBDD
from flamapy.metamodels.bdd_metamodel.operations import BDDProductsNumber

from fm_solver.utils import utils, fm_utils, constraints_utils
from fm_solver.transformations import FMSansReader
from fm_solver.operations import FMConfigurationsNumber


#sys.setrecursionlimit(10000)
OUTPUT_FILE = 'models_stats.csv'


def get_fm_filepath_models(dir: str) -> list[str]:
    """Get all models from the given directory."""
    models = []
    for root, dirs, files in os.walk(dir):
        for file in files:
            filepath = os.path.join(root, file)
            models.append(filepath)
    return models


def main(fm_filepath: str, n_cores: int):
    # Get feature model name
    path, filename = os.path.split(fm_filepath)
    filename = '.'.join(filename.split('.')[:-1])

    # Output file for raw data
    output_file = os.path.join(path, OUTPUT_FILE)

    # Load the feature model
    print(f'Reading feature model from {fm_filepath}')
    fm = None
    fmsans = None
    if fm_filepath.endswith('.uvl'):
        fm = UVLReader(fm_filepath).transform()
    elif fm_filepath.endswith('.json'):
        fmsans = FMSansReader(fm_filepath).transform()
    else:
        print(f'Skipped file {fm_filepath}')
        return None

    if fm is not None:
        print(f'Analyzing metrics...')
        n_features = len(fm.get_features())
        print(f'#Features:             {n_features}')
        n_abstract_features = sum(f.is_abstract for f in fm.get_features())
        n_concrete_features = n_features - n_abstract_features
        print(f'  #Concrete features:  {n_concrete_features}')
        print(f'  #Abstract features:  {n_abstract_features}')
        n_auxiliary_features = sum(fm_utils.is_auxiliary_feature(f) for f in fm.get_features())
        print(f'  #Auxiliary features: {n_auxiliary_features}')
        n_ctcs = len(fm.get_constraints())
        print(f'#Constraints:          {n_ctcs}')
        n_ctcs_simple = sum(constraints_utils.is_simple_constraint(ctc) for ctc in fm.get_constraints())    
        print(f'  #Simple CTCs:        {n_ctcs_simple}')
        n_requires_ctcs = sum(constraints_utils.is_requires_constraint(ctc) for ctc in fm.get_constraints())
        n_excludes_ctcs = n_ctcs_simple - n_requires_ctcs
        print(f'    #Requires:         {n_requires_ctcs}')
        print(f'    #Excludes:         {n_excludes_ctcs}')
        n_ctcs_complex = n_ctcs - n_ctcs_simple
        print(f'  #Complex CTCs:       {n_ctcs_complex}')
        n_pseudo_ctcs = sum(constraints_utils.is_pseudo_complex_constraint(ctc) for ctc in fm.get_constraints())
        n_strict_ctcs = n_ctcs_complex - n_pseudo_ctcs
        print(f'    #Pseudo:           {n_pseudo_ctcs}')
        print(f'    #Strict:           {n_strict_ctcs}')

        print(f'Analyzing semantics...')
        if fm.get_constraints():
            print(f'Transforming FM to BDD...')
            bdd_model = FmToBDD(fm).transform()
            print(f'Computing products number using the BDD...')
            n_configs = BDDProductsNumber().execute(bdd_model).get_result()
        else:
            print(f'Computing products number using the FM structure...')
            n_configs = FMConfigurationsNumber().execute(fm).get_result()
        n_configs_scientific = utils.int_to_scientific_notation(n_configs)
        n_configs_pretty = n_configs_scientific if n_configs > 10e6 else n_configs    
        print(f'#Configs:             {n_configs} ({n_configs_scientific})')

        # Save stats in file
        if not os.path.exists(output_file):
            with open(output_file, 'w', encoding='utf8') as file:
                file.write(f'Model, F, Fc, Fa, Faux, CTC, CTCs, CTCreq, CTCexc, CTCc, CTCpseudo, CTCstrict, #Configs{os.linesep}')
        with open(output_file, 'a', encoding='utf8') as file:
            file.write(f'{filename}, {n_features}, {n_concrete_features}, {n_abstract_features}, {n_auxiliary_features}, {n_ctcs}, {n_ctcs_simple}, {n_requires_ctcs}, {n_excludes_ctcs}, {n_ctcs_complex}, {n_pseudo_ctcs}, {n_strict_ctcs}, {n_configs_pretty}{os.linesep}')
            
    elif fmsans is not None:
        n_subtrees = len(fmsans.transformations_ids)
        print(f'#Subtrees:            {n_subtrees}')
        subtrees = fmsans.get_subtrees(n_cores)
        features_subtrees = [len(st.get_features()) for st in subtrees]
        min_features_subtrees = min(features_subtrees)
        max_features_subtrees = max(features_subtrees)
        median_features_subtrees = round(statistics.median(features_subtrees), 2)
        mean_features_subtrees = round(statistics.mean(features_subtrees), 2)
        stdev_features_subtrees = round(statistics.stdev(features_subtrees), 2) if len(features_subtrees) > 1 else 0
        print(f'  #Min features:      {min_features_subtrees}')
        print(f'  #Max features:      {max_features_subtrees}')
        print(f'  #Median features:   {median_features_subtrees}')
        print(f'  #Mean features:     {mean_features_subtrees}')
        print(f'  #Stdev features:    {stdev_features_subtrees}')
        
        print(f'Analyzing semantics...')
        print(f'Obtaining GFT...')
        gft = fmsans.get_feature_model(n_cores)
        print(f'Computing products number using the FM structure...')
        n_configs = FMConfigurationsNumber().execute(gft).get_result()    
        n_configs_scientific = utils.int_to_scientific_notation(n_configs)
        n_configs_pretty = n_configs_scientific if n_configs > 10e6 else n_configs    
        print(f'#Configs:             {n_configs} ({n_configs_scientific})')

        # Save stats in file
        if not os.path.exists(output_file):
            with open(output_file, 'w', encoding='utf8') as file:
                file.write(f'Model, Subtrees, Fmin, Fmax, Fmedian, Fmean, Fstdev, #Configs{os.linesep}')
        with open(output_file, 'a', encoding='utf8') as file:
            file.write(f'{filename}, {n_subtrees}, {min_features_subtrees}, {max_features_subtrees}, {median_features_subtrees}, {mean_features_subtrees}, {stdev_features_subtrees}, {n_configs_pretty}{os.linesep}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Returns the stats of an FM.')
    input_model = parser.add_mutually_exclusive_group(required=True)
    input_model.add_argument('-d', '--dir', dest='dir', type=str, help='Input directory with the models in the same format (.uvl or .json) to be analyzed.')
    input_model.add_argument('-fm', '--featuremodel', dest='feature_model', type=str, help='Input feature model in UVL (.uvl) or FMSans (.json) format.')
    parser.add_argument('-c', '--cores', dest='n_cores', type=int, required=False, default=1, help='Number of cores (processes) to execute (power of 2) (default = 1).')
    args = parser.parse_args()

    if args.n_cores <= 0 or not math.log(args.n_cores, 2).is_integer():
        if args.n_cores == multiprocessing.cpu_count():
            sys.exit(f'The number of cores of this computer is not a power of 2. Please set the -c parameter to a power of 2.')
        else:
            sys.exit(f'The number of cores must be positive and power of 2.')

    if args.feature_model:
        main(args.feature_model, args.n_cores)
    elif args.dir:
        models = get_fm_filepath_models(args.dir)
        for filepath in models:
            main(filepath, args.n_cores)