import os
import pytest

from flamapy.metamodels.fm_metamodel.transformations import UVLReader

from flamapy.metamodels.bdd_metamodel.transformations import FmToBDD
from flamapy.metamodels.bdd_metamodel.operations import (
    BDDProductsNumber
)

from fm_solver.models.feature_model import FM
from fm_solver.transformations import FMToFMSans
from fm_solver.operations import (
    FMFullAnalysis
)


#TESTING_MODELS_DIR = 'models/pizzas_tests/'
#TESTING_MODELS_DIR = 'models/paper_tests/'
TESTING_MODELS_DIR = 'models/ESLR/'
N_CORES = 8


def get_fm_filepath_models() -> list[str]:
    """Get all models from the testing models directory."""
    models = []
    for root, dirs, files in os.walk(TESTING_MODELS_DIR):
        for file in files:
            filepath = os.path.join(root, file)
            models.append(filepath)
    return models


@pytest.mark.parametrize('fm_filepath', get_fm_filepath_models())
def test_nof_configurations(fm_filepath: str):
    """Test that the number of configurations of our approach is the same as returned by an BDD."""
    # Load the feature model
    feature_model = UVLReader(fm_filepath).transform()

    # Get the BDD model
    bdd_model = FmToBDD(feature_model).transform()
    expected_n_configs = BDDProductsNumber().execute(bdd_model).get_result()

    # Get the fmsans model
    fm = FM.from_feature_model(feature_model)
    fmsans_model = FMToFMSans(fm, n_cores=N_CORES).transform()
    result = fmsans_model.get_analysis()
    n_configs = result[FMFullAnalysis.CONFIGURATIONS_NUMBER]
    
    assert n_configs == expected_n_configs
