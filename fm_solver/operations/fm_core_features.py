from flamapy.metamodels.fm_metamodel.models import FeatureModel, Feature

from fm_solver.operations import FMOperation


class FMCoreFeatures(FMOperation):
    """Core features are features that are present in all configurations of the feature model."""

    @staticmethod
    def get_name() -> str:
        return 'Core features'

    def __init__(self) -> None:
        self.result: list[Feature] = []
        self.feature_model = None

    def get_result(self) -> list[Feature]:
        return self.result

    def execute(self, model: FeatureModel) -> 'FMCoreFeatures':
        self.feature_model = model
        self.result = get_core_features(model)
        return self

    def get_core_features(self) -> set[Feature]:
        return get_core_features(self.feature_model)


def get_core_features(feature_model: FeatureModel) -> set[Feature]:
    if feature_model.root is None:
        return set()

    # Get core features from the tree structure
    core_features = set()
    core_features.add(feature_model.root)
    features = [feature_model.root]
    while features:
        feature = features.pop()
        for relation in feature.get_relations():
            if relation.is_mandatory():
                core_features.update(relation.children)
                features.extend(relation.children)

    return core_features
