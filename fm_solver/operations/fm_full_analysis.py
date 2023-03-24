import statistics
from typing import Any

from fm_solver.models.feature_model import FM
from fm_solver.operations import FMOperation
from fm_solver.operations import (
    FMConfigurationsNumber,
    FMCoreFeatures,
    FMDeadFeatures
)


class FMFullAnalysis(FMOperation):
    """Meta operation that returns the result of several other operations."""

    N_FEATURES = '#Features'
    MIN_FEATURES = 'FeaturesMin'
    MAX_FEATURES = 'FeaturesMax'
    MEDIAN_FEATURES = 'FeaturesMedian'
    MEAN_FEATURES = 'FeaturesMean'
    STDEV_FEATURES = 'FeaturesStdev'

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
    def join_results(subtrees_results: list[dict[str, Any]], fm: FM) -> dict[str, Any]:
        if not subtrees_results:
            return {FMConfigurationsNumber.get_name(): 0, 
                    FMCoreFeatures.get_name(): set(),
                    FMFullAnalysis.MIN_FEATURES: 0,
                    FMFullAnalysis.MAX_FEATURES: 0,
                    FMFullAnalysis.MEDIAN_FEATURES: 0,
                    FMFullAnalysis.MEAN_FEATURES: 0,
                    FMFullAnalysis.STDEV_FEATURES: 0}
                    #FMDeadFeatures.get_name(): set()}
                    
        result = {}
        result[FMConfigurationsNumber.get_name()] = FMConfigurationsNumber.join_results([r[FMConfigurationsNumber.get_name()] for r in subtrees_results])
        result[FMCoreFeatures.get_name()] = FMCoreFeatures.join_results([r[FMCoreFeatures.get_name()] for r in subtrees_results])
        #result[FMDeadFeatures.get_name()] = FMDeadFeatures.join_results([r[FMDeadFeatures.get_name()] for r in subtrees_results], fm)
        values = [r[FMFullAnalysis.N_FEATURES] for r in subtrees_results]
        result[FMFullAnalysis.MIN_FEATURES] = min(values)
        result[FMFullAnalysis.MAX_FEATURES] = max(values)
        result[FMFullAnalysis.MEDIAN_FEATURES] = round(statistics.median(values), 2)
        result[FMFullAnalysis.MEAN_FEATURES] = round(statistics.mean(values), 2)
        result[FMFullAnalysis.STDEV_FEATURES] = round(statistics.stdev(values), 2) if len(values) > 1 else 0
        return result


def get_full_analysis(feature_model: FM) -> dict[str, Any]:
    if feature_model is None or feature_model.root is None:
        return {}
    
    result = {}
    # Number of configurations
    n_configurations = FMConfigurationsNumber().execute(feature_model).get_result()
    result[FMConfigurationsNumber.get_name()] = n_configurations

    # Core features
    core_features = FMCoreFeatures().execute(feature_model).get_result()
    result[FMCoreFeatures.get_name()] = core_features

    # Dead features
    #dead_features = FMDeadFeatures().execute(feature_model).get_result()
    #result[FMDeadFeatures.get_name()] = dead_features

    # Stats
    result[FMFullAnalysis.N_FEATURES] = len(feature_model.get_features())

    return result
