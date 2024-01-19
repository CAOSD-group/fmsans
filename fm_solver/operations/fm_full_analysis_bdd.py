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
    BDDProductsNumber
)


class FMFullAnalysisBDD(FMOperation):
    """Meta operation that returns the result of several other operations performed with the BDD."""

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
    def join_results(subtrees_results: list[dict[str, Any]], fm: FM) -> dict[str, Any]:
        if not subtrees_results:
            return {FMConfigurationsNumber.get_name(): 0, 
                    FMCoreFeatures.get_name(): set()}
                    #FMDeadFeatures.get_name(): set()}
        result = {}
        result[FMConfigurationsNumber.get_name()] = FMConfigurationsNumber.join_results([r[FMConfigurationsNumber.get_name()] for r in subtrees_results])
        result[FMCoreFeatures.get_name()] = FMCoreFeatures.join_results([r[FMCoreFeatures.get_name()] for r in subtrees_results])
        #result[FMDeadFeatures.get_name()] = FMDeadFeatures.join_results([r[FMDeadFeatures.get_name()] for r in subtrees_results], fm)
        return result


def get_full_analysis(feature_model: BDDModel) -> dict[str, Any]:
    if feature_model is None:
        return {}
    
    result = {}
    # Number of configurations
    n_configurations = BDDProductsNumber().execute(feature_model).get_result()
    result[FMConfigurationsNumber.get_name()] = n_configurations

    # Core features
    core_features = BDDCoreFeatures().execute(feature_model).get_result()
    result[FMCoreFeatures.get_name()] = set(core_features)

    # Dead features
    #dead_features = BDDDeadFeatures().execute(feature_model).get_result()
    #result[FMDeadFeatures.get_name()] = set(dead_features)

    return result
