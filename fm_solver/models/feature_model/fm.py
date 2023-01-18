from typing import Optional

from flamapy.metamodels.fm_metamodel.models import (
    FeatureModel, 
    Feature, 
    Relation,
    Constraint
)


class FM(FeatureModel):

    AUXILIARY_FEATURES_ATTRIBUTE = 'aux'

    def __init__(self, root: Feature, constraints: Optional[list[Constraint]] = None) -> None:
        super().__init__(root, constraints)
        self._features: set[Feature] = {f for f in super().get_features()}
        self._feature_by_name: dict[str, Feature] = {f.name: f for f in self.get_features()}
        #self._commitment_features: set[Feature] = set()  # only for optimization.

    @classmethod
    def from_feature_model(cls, feature_model: FeatureModel) -> 'FM': 
        return FM(feature_model.root, feature_model.ctcs)

    def get_features(self) -> list[Feature]:
        return self._features

    def get_feature_by_name(self, feature_name: str) -> Optional[Feature]:
        return self._feature_by_name.get(feature_name, None)

    def delete_feature(self, feature_name: str) -> 'FM':
        """Given a feature diagram T and a feature F, this algorithm computes T(-F) 
        whose products are precisely those products of T with do not contain F.

        The algorithm is an adaptation from:
            [Broek2008 @ SPLC: Elimination of constraints from feature trees].
        """
        feature = self.get_feature_by_name(feature_name)
        if feature is not None:  # Step 1. If T does not contain F, the result is T.
            feature_to_delete = feature
            parent = feature_to_delete.get_parent()  # Step 2. Let the parent feature of F be P.
            # Step 3. If P is a MandOpt feature and F is a mandatory subfeature of P, 
            # GOTO step 4 with P instead of F.
            while feature_to_delete != self.root and not parent.is_group() and feature_to_delete.is_mandatory():
                feature_to_delete = parent
                parent = feature_to_delete.get_parent()
            if feature_to_delete == self.root:  # If F is the root of T, the result is NIL.
                self._clear_model()
                return None
            # If P is a MandOpt feature and F is an optional subfeature of P, delete F.
            elif not parent.is_group() and feature_to_delete.is_optional():
                rel = next((r for r in parent.get_relations() if feature_to_delete in r.children), None)
                parent.get_relations().remove(rel)
                self._delete_feature_branch(feature_to_delete)
            # If P is an Xor feature or an Or feature, delete F; if P has only one remaining subfeature, 
            # make P a MandOpt feature and its subfeature a mandatory subfeature.
            elif parent.is_alternative_group() or parent.is_or_group():
                rel = parent.get_relations()[0]
                rel.children.remove(feature_to_delete)
                self._delete_feature_branch(feature_to_delete)
                if rel.card_max > 1:
                    rel.card_max -= 1
        return self

    def add_feature(self, feature: Feature) -> None:
        self._features.add(feature)
        self._feature_by_name[feature.name] = feature

    def commit_feature(self, feature_name: str) -> 'FM':
        """Given a feature diagram T and a feature F, this algorithm computes T(+F) 
        whose products are precisely those products of T with contain F.

        The algorithm is an adaptation from:
            [Broek2008 @ SPLC: Elimination of constraints from feature trees].
        """
        feature = self.get_feature_by_name(feature_name) 
        # Step 1. If T does not contain F, the result is NIL.
        if feature is None:
            self._clear_model()
            return None
        else:
            feature_to_commit = feature
            while feature_to_commit != self.root:  # Step 2. If F is the root of T, the result is T.
                parent = feature_to_commit.get_parent()  # Step 3. Let the parent feature of F be P.
                # If P is a MandOpt feature and F is an optional subfeature, 
                # make F a mandatory subfeature of P.
                if not parent.is_group() and feature_to_commit.is_optional():  
                    rel = next((r for r in parent.get_relations() if feature_to_commit in r.children), None)
                    rel.card_min = 1
                # If P is an Xor feature, 
                # make P a MandOpt feature which has F as single mandatory subfeature 
                # and has no optional subfeatures. All other subfeatures of P are removed from the tree.
                elif parent.is_alternative_group(): 
                    for child in parent.get_children():
                        if child != feature_to_commit:
                            self._delete_feature_branch(child)
                    parent.get_relations()[0].children = [feature_to_commit]
                # If P is an Or feature, 
                # make P a MandOpt feature which has F as single mandatory subfeature, 
                # and has all other subfeatures of P as optional subfeatures.
                elif parent.is_or_group():  
                    parent_relations = parent.get_relations()
                    or_relation = parent_relations[0]
                    or_relation.children.remove(feature_to_commit)
                    parent_relations.remove(or_relation)
                    new_mandatory_rel = Relation(parent, [feature_to_commit], 1, 1)
                    parent_relations.append(new_mandatory_rel)
                    for child in or_relation.children:
                        new_optional_rel = Relation(parent, [child], 0, 1)
                        parent_relations.append(new_optional_rel)
                # Step 4. GOTO step 2 with P instead of F.
                feature_to_commit = parent
        return self

    def _delete_feature_branch(self, root: Feature) -> None:
        """Delete the current feature and all children of the specified feature."""
        features = [root]
        while features:
            f = features.pop()
            self._features.remove(f)
            self._feature_by_name.pop(f.name)
            features.extend(f.get_children())

    def _clear_model(self) -> None:
        self.root = None
        self._features.clear()
        self._feature_by_name.clear()
