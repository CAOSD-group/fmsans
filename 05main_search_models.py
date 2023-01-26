import os
import argparse

from flamapy.metamodels.fm_metamodel.transformations import UVLReader

from fm_solver.models.feature_model import FM
from fm_solver.utils import constraints_utils


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

    for i, fm_filepath in enumerate(models_filepaths, 1):
        try:
            # Load the feature model
            feature_model = UVLReader(fm_filepath).transform()

            # Get stats
            fm = FM.from_feature_model(feature_model)
            n_features = len(fm.get_features())
            n_concrete_features = sum(not f.is_abstract for f in fm.get_features())
            n_abstract_features = sum(f.is_abstract for f in fm.get_features())
            n_ctcs = len(fm.get_constraints())
            n_ctcs_complex = sum(constraints_utils.is_complex_constraint(ctc) for ctc in fm.get_constraints())
            n_ctcs_simple = sum(constraints_utils.is_simple_constraint(ctc) for ctc in fm.get_constraints())
            n_pseudo_ctcs = sum(len(constraints_utils.split_constraint(ctc)) > 1 for ctc in fm.get_constraints())
            n_strict_ctcs = n_ctcs_complex - n_pseudo_ctcs
            n_requires_ctcs = sum(constraints_utils.is_requires_constraint(ctc) for ctc in fm.get_constraints())
            n_excludes_ctcs = sum(constraints_utils.is_excludes_constraint(ctc) for ctc in fm.get_constraints())

            print(f'FM {i}: {fm_filepath}. F:{n_features} (Fc:{n_concrete_features}, Fa:{n_abstract_features}), CTC:{n_ctcs} (CTCc:{n_ctcs_complex} (Strict:{n_strict_ctcs}, Pseudo:{n_pseudo_ctcs}), CTCs:{n_ctcs_simple} (Req:{n_requires_ctcs}, Exc:{n_excludes_ctcs}))')
        except Exception as e:
            print(e)
            print(f'Error in model: {fm_filepath}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyze the stats of all models in the given folder.')
    parser.add_argument(dest='dir', type=str, help='Folder with the models.')
    args = parser.parse_args()

    main(args.dir)
