import os
import argparse
import subprocess
import locale

from flamapy.metamodels.fm_metamodel.transformations import UVLReader

from fm_solver.models.feature_model import FM
from fm_solver.utils import constraints_utils


TIMEOUT = 1800
COMMAND = ['python', '00main.py', '-fm']


def get_fm_filepath_models(dir: str) -> list[str]:
    """Get all models from the given directory."""
    models = []
    for root, dirs, files in os.walk(dir):
        for file in files:
            filepath = os.path.join(root, file)
            models.append(filepath)
    return models

    
def main(dir: str):
    models_filepaths = get_fm_filepath_models(dir)

    models = set()
    for i, fm_filepath in enumerate(models_filepaths, 1):
        try:
            if fm_filepath.endswith('.uvl'):
                # Load the feature model
                feature_model = UVLReader(fm_filepath).transform()

                # Get stats
                fm = FM.from_feature_model(feature_model)
                n_ctcs = len(fm.get_constraints())
                n_features = len(fm.get_features())
                n_basic_ctcs = sum(constraints_utils.is_simple_constraint(ctc) for ctc in fm.get_constraints())
                n_complex_ctcs = n_ctcs - n_basic_ctcs
                # Get feature model name
                path, filename = os.path.split(fm_filepath)
                filename = '.'.join(filename.split('.')[:-1])
                if filename not in models:
                    models.add(filename)
                    print(f'{filename}, {n_features}, {n_ctcs}')
                #if n_ctcs > 10:
                    #command = COMMAND + [fm_filepath]
                    #print(f'FM {i}: {fm_filepath}. #Constraints: {n_ctcs} ({sum(constraints_utils.is_simple_constraint(ctc) for ctc in fm.get_constraints())})')
                    #process = subprocess.run(args=command, stdout=subprocess.PIPE, timeout=TIMEOUT) #, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(e)
            print(f'Error in model: {fm_filepath}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyze the stats of all models in the given folder.')
    parser.add_argument(dest='dir', type=str, help='Folder with the models.')
    args = parser.parse_args()

    main(args.dir)
