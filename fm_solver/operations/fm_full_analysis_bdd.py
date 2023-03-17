from typing import Any

from fm_solver.models.feature_model import FM
from fm_solver.operations import FMOperation
from fm_solver.operations import (
    FMConfigurationsNumber,
    FMCoreFeatures,
    FMDeadFeatures
)

from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.operations import (
    BDDProductsNumber,
    BDDCoreFeatures,
    BDDDeadFeatures
)


class FMFullAnalysisBDD(FMOperation):
    """Meta operation that returns the result of several other operations performed with the BDD."""

    CONFIGURATIONS_NUMBER = '#Configurations'
    CORE_FEATURES = 'Core features'
    DEAD_FEATURES = 'Dead features'

    @staticmethod
    def get_name() -> str:
        return 'Full analysis'

    def __init__(self) -> None:
        self.result: dict[str, Any] = {}
        self.feature_model = None

    def get_result(self) -> dict[str, Any]:
        return self.result

    def execute(self, model: BDDModel) -> 'FMFullAnalysisBDD':
        self.feature_model = model
        self.result = get_full_analysis(model)
        return self

    def get_full_analysis(self) -> dict[str, Any]:
        return get_full_analysis(self.feature_model)

    @staticmethod
    def join_results(subtrees_results: list[dict[str, Any]]) -> dict[str, Any]:
        if not subtrees_results:
            return {FMFullAnalysisBDD.CONFIGURATIONS_NUMBER: 0, 
                    FMFullAnalysisBDD.CORE_FEATURES: set(),
                    FMFullAnalysisBDD.DEAD_FEATURES: set()}
        result = {}
        result[FMFullAnalysisBDD.CONFIGURATIONS_NUMBER] = FMConfigurationsNumber.join_results([r[FMFullAnalysisBDD.CONFIGURATIONS_NUMBER] for r in subtrees_results])
        result[FMFullAnalysisBDD.CORE_FEATURES] = FMCoreFeatures.join_results([r[FMFullAnalysisBDD.CORE_FEATURES] for r in subtrees_results])
        result[FMFullAnalysisBDD.DEAD_FEATURES] = FMDeadFeatures.join_results([r[FMFullAnalysisBDD.DEAD_FEATURES] for r in subtrees_results])
        return result


def get_full_analysis(feature_model: BDDModel) -> dict[str, Any]:
    if feature_model is None:
        return {}
    
    result = {}
    # Number of configurations
    n_configurations = BDDProductsNumber().execute(feature_model).get_result()
    result[FMFullAnalysisBDD.CONFIGURATIONS_NUMBER] = n_configurations

    # Core features
    core_features = BDDCoreFeatures().execute(feature_model).get_result()
    result[FMFullAnalysisBDD.CORE_FEATURES] = set(core_features)

    # Dead features
    dead_features = BDDDeadFeatures().execute(feature_model).get_result()
    result[FMFullAnalysisBDD.DEAD_FEATURES] = set(dead_features)

    return result
