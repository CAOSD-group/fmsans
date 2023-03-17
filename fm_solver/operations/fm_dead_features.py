from flamapy.metamodels.fm_metamodel.models import Feature

from fm_solver.models.feature_model import FM
from fm_solver.operations import FMOperation
from fm_solver.utils import fm_utils


class FMDeadFeatures(FMOperation):
    """Dead features are features that are not present in all configurations of the feature model.
    
    However, for our subtrees, dead features are those present in the original feature tree that are not present in any subtree."""

    @staticmethod
    def get_name() -> str:
        return 'Dead features'

    def __init__(self) -> None:
        self.result: set[Feature] = ()
        self.feature_model = None

    def get_result(self) -> set[Feature]:
        return self.result

    def execute(self, model: FM) -> 'FMDeadFeatures':
        self.feature_model = model
        self.result = get_dead_features(self.feature_model)
        return self

    def get_dead_features(self) -> set[Feature]:
        return get_dead_features(self.feature_model)

    @staticmethod
    def join_results(subtrees_results: list[set[Feature]], fm: FM) -> set[Feature]:
        features = {f for f in fm.get_features() if not fm_utils.is_auxiliary_feature(f)}
        return features.difference(set.union(*subtrees_results))


def get_dead_features(feature_model: FM) -> set[Feature]:
    """ In a feature model without constraints there is no dead features."""
    return set(feature_model.get_features())  #{f for f in feature_model.get_features() if not fm_utils.is_auxiliary_feature(f)}
