from typing import Any

from fm_solver.models.feature_model import FM
from fm_solver.operations import FMOperation
from fm_solver.operations import (
    FMConfigurationsNumber,
    FMCoreFeatures
)

from flamapy.metamodels.pysat_metamodel.models import PySATModel
from flamapy.metamodels.pysat_metamodel.operations import (
    SATProductsNumber,
    SATCoreFeatures,
    SATDeadFeatures
)


class FMFullAnalysisSAT(FMOperation):
    """Meta operation that returns the result of several other operations performed with the SAT solver."""

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

    def execute(self, model: PySATModel) -> 'FMFullAnalysisSAT':
        self.feature_model = model
        self.result = get_full_analysis(model)
        return self

    def get_full_analysis(self) -> dict[str, Any]:
        return get_full_analysis(self.feature_model)

    @staticmethod
    def join_results(subtrees_results: list[dict[str, Any]]) -> dict[str, Any]:
        if not subtrees_results:
            return {FMFullAnalysisSAT.CONFIGURATIONS_NUMBER: 0, 
                    FMFullAnalysisSAT.CORE_FEATURES: set(),
                    FMFullAnalysisSAT.DEAD_FEATURES: set()}
        result = {}
        result[FMFullAnalysisSAT.CONFIGURATIONS_NUMBER] = FMConfigurationsNumber.join_results([r[FMFullAnalysisSAT.CONFIGURATIONS_NUMBER] for r in subtrees_results])
        result[FMFullAnalysisSAT.CORE_FEATURES] = FMCoreFeatures.join_results([r[FMFullAnalysisSAT.CORE_FEATURES] for r in subtrees_results])
        result[FMFullAnalysisSAT.DEAD_FEATURES] = FMCoreFeatures.join_results([r[FMFullAnalysisSAT.DEAD_FEATURES] for r in subtrees_results])
        return result


def get_full_analysis(feature_model: PySATModel) -> dict[str, Any]:
    if feature_model is None:
        return {}
    
    result = {}
    # Number of configurations
    n_configurations = SATProductsNumber().execute(feature_model).get_result()
    result[FMFullAnalysisSAT.CONFIGURATIONS_NUMBER] = n_configurations

    # Core features
    core_features = SATCoreFeatures().execute(feature_model).get_result()
    result[FMFullAnalysisSAT.CORE_FEATURES] = set(core_features)

    # Dead features
    dead_feature = SATDeadFeatures().execute(feature_model).get_result()
    result[FMFullAnalysisSAT.DEAD_FEATURES] = set(dead_feature)
    return result
