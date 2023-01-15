from typing import Any

from fm_solver.models.feature_model import FM
from fm_solver.operations import FMOperation
from fm_solver.operations import (
    FMConfigurationsNumber,
    FMCoreFeatures
)


class FMFullAnalysis(FMOperation):
    """Meta operation that returns the result of several other operations."""

    CONFIGURATIONS_NUMBER = '#Configurations'
    CORE_FEATURES = 'Core features'

    @staticmethod
    def get_name() -> str:
        return 'Full analysis'

    def __init__(self) -> None:
        self.result: dict[str, Any] = {}
        self.feature_model = None

    def get_result(self) -> dict[str, Any]:
        return self.result

    def execute(self, model: FM) -> 'FMFullAnalysis':
        self.feature_model = model
        self.result = get_full_analysis(model)
        return self

    def get_full_analysis(self) -> dict[str, Any]:
        return get_full_analysis(self.feature_model)

    @staticmethod
    def join_results(subtrees_results: list[dict[str, Any]]) -> dict[str, Any]:
        if not subtrees_results:
            return {FMFullAnalysis.CONFIGURATIONS_NUMBER: 0, 
                    FMFullAnalysis.CORE_FEATURES: set()}
        result = {}
        result[FMFullAnalysis.CONFIGURATIONS_NUMBER] = FMConfigurationsNumber.join_results([r[FMFullAnalysis.CONFIGURATIONS_NUMBER] for r in subtrees_results])
        result[FMFullAnalysis.CORE_FEATURES] = FMCoreFeatures.join_results([r[FMFullAnalysis.CORE_FEATURES] for r in subtrees_results])
        return result


def get_full_analysis(feature_model: FM) -> dict[str, Any]:
    if feature_model is None or feature_model.root is None:
        return {}
    
    result = {}
    # Number of configurations
    n_configurations = FMConfigurationsNumber().execute(feature_model).get_result()
    result[FMFullAnalysis.CONFIGURATIONS_NUMBER] = n_configurations

    # Core features
    core_features = FMCoreFeatures().execute(feature_model).get_result()
    result[FMFullAnalysis.CORE_FEATURES] = core_features

    return result
