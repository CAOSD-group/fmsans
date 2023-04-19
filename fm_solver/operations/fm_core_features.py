from flamapy.metamodels.fm_metamodel.models import Feature

from fm_solver.models.feature_model import FM
from fm_solver.operations import FMOperation
from fm_solver.utils import fm_utils


class FMCoreFeatures(FMOperation):
    """Core features are features that are present in all configurations of the feature model."""

    @staticmethod
    def get_name() -> str:
        return 'Core features'

    def __init__(self) -> None:
        self.result: set[str] = set()
        self.feature_model = None

    def get_result(self) -> set[str]:
        return self.result

    def execute(self, model: FM) -> 'FMCoreFeatures':
        self.feature_model = model
        self.result = get_core_features(model)
        return self

    def get_core_features(self) -> set[str]:
        return get_core_features(self.feature_model)

    @staticmethod
    def join_results(subtrees_results: list[set[str]]) -> set[str]:
        return set.intersection(*subtrees_results)


def get_core_features(feature_model: FM) -> set[str]:
    if feature_model.root is None:
        return set()

    # Get core features from the tree structure
    core_features = set()
    features: list[str] = []
    root = feature_model.root
    if not fm_utils.is_auxiliary_feature(root):
        core_features.add(root.name)
    features.append(root)
    while features:
        feature = features.pop()        
        for relation in feature.get_relations():
            aux_feature = fm_utils.is_auxiliary_feature(feature)
            if relation.is_mandatory():  # it is a core feature 
                if not aux_feature:
                    core_features.update([c.name for c in relation.children])
                features.extend(relation.children)
            elif aux_feature and relation.is_alternative():
                core_features.update(set.intersection(*[get_core_features(FM(child)) for child in relation.children]))
    return core_features
