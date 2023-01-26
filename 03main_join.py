import argparse

from flamapy.metamodels.fm_metamodel.transformations import UVLReader

from fm_solver.models import FMSans
from fm_solver.models.feature_model import FM
from fm_solver.transformations import FMSansReader, FMSansWriter
from fm_solver.utils import fm_utils, utils
from fm_solver.operations import FMFullAnalysis


def main(dirpath: str) -> None:
    # Get all models
    print(f'Getting models from {dirpath}...')
    filespaths = utils.get_filespaths(dirpath)

    if not filespaths:
        print(f'There is not any models to join in the given path: {dirpath}.')
        return None

    # Join models
    join_model = None
    filename = None
    print(f'Joining {len(filespaths)} models...')
    for i, filepath in enumerate(filespaths, 1):
        print(f'{i} ', end='', flush=True)
        fmsans_model = FMSansReader(filepath).transform()
        if fmsans_model.transformations_ids is not None:
            if join_model is None:
                join_model = fmsans_model
                filename = utils.get_filename_from_filepath(filepath)
            join_model.transformations_ids.update(fmsans_model.transformations_ids)
    print()
    print(f'#Subtrees: {len(join_model.transformations_ids)}')

    # Serializing the FMSans model
    print(f'Serializing model...')
    parts_name = filename.split('_')
    n_tasks = parts_name[-1].split('-')[1]
    n_cores = parts_name[-2]
    fm_name = '_'.join(parts_name[:-2])
    output_fmsans_filepath = f'{fm_name}_{n_cores}_{n_tasks}.json'
    FMSansWriter(output_fmsans_filepath, join_model).transform()

    print(f'Analyzing model...')
    # Get number of configurations
    #result = join_model.get_analysis()
    #n_configs = result[FMFullAnalysis.CONFIGURATIONS_NUMBER]
    n_configs = join_model.get_number_of_configurations(8)
    print(f'Configs: {n_configs} ({utils.int_to_scientific_notation(n_configs)})')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Join all FMSans (.json) in a folder.')
    parser.add_argument(dest='dirpath', type=str, help='Folder with the models.')
    args = parser.parse_args()

    main(args.dirpath)
