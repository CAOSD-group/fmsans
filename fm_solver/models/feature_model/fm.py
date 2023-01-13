from typing import Any, Optional

from flamapy.metamodels.fm_metamodel.models import (
    FeatureModel, 
    Feature, 
    Relation, 
    Constraint, 
    Attribute
)

class FM(FeatureModel):

    def __init__(self, root: Feature, constraints: Optional[list[Constraint]] = None) -> None:
        super().__init__(root, constraints)
        self._features: set[Feature] = {f for f in super().get_features()}
        self._feature_by_name: dict[str, Feature] = {f.name: f for f in self.get_features()}

    @classmethod
    def from_feature_model(cls, feature_model: FeatureModel) -> 'FM': 
        return FM(feature_model.root, feature_model.ctcs)

    def get_features(self) -> list[Feature]:
        return self._features

    def get_feature_by_name(self, feature_name: str) -> Optional[Feature]:
        return self._feature_by_name.get(feature_name, None)

    def add_feature(self, feature: Feature) -> None:
        self._features.add(feature)
        self._feature_by_name[feature.name] = feature

    def delete_feature(self, feature: Feature) -> None:
        self._features.remove(feature)
        self._feature_by_name.pop(feature.name)

    def delete_branch(self, feature: Feature) -> None:
        """Delete all children of the specified feature."""
        features = [feature]
        while features:
            f = features.pop()
            features.extend(f.get_children())
            self.delete_feature(f)
