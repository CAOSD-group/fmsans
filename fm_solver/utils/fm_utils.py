"""
This module contains all utils related to the management of a feature model.
"""

import copy
from collections.abc import Callable

from flamapy.metamodels.fm_metamodel.models import FeatureModel, Relation


def commitment_feature(feature_model: FeatureModel, feature_name: str) -> FeatureModel:
    """Given a feature diagram T and a feature F, 
    this algorithm computes the feature model T(+F) 
    whose products are precisely those products of T with contain F.
    
    The algorithm transforms T into T(+F).

    The algorithm is an adaptation from:
        [Broek2008 @ SPLC: Elimination of constraints from feature trees].
    """
    feature = feature_model.get_feature_by_name(feature_name)
    # Step 1. If T does not contain F, the result is NIL.
    if feature not in feature_model.get_features():
        return None
    feature_to_commit = feature
    # Step 2. If F is the root of T, the result is T.
    while feature_to_commit != feature_model.root:
        # Step 3. Let the parent feature of F be P.
        parent = feature_to_commit.get_parent()  
        # If P is a MandOpt feature and F is an optional subfeature, 
        # make F a mandatory subfeature of P.
        if not parent.is_group() and feature_to_commit.is_optional():  
            rel = next((r for r in parent.get_relations() if feature_to_commit in r.children), None)
            rel.card_min = 1
        # If P is an Xor feature, 
        # make P a MandOpt feature which has F as single mandatory subfeature 
        # and has no optional subfeatures. All other subfeatures of P are removed from the tree.
        elif parent.is_alternative_group():  
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
    return feature_model


def deletion_feature(feature_model: FeatureModel, feature_name: str) -> FeatureModel:
    """Given a feature diagram T and a feature F,
    this algorithm computes the feature model T(-F) 
    whose products are precisely those products of T with do not contain F.
    
    The algorithm transforms T into T(-F).

    The algorithm is an adaptation from:
        [Broek2008 @ SPLC: Elimination of constraints from feature trees].
    """
    feature = feature_model.get_feature_by_name(feature_name)
    # Step 1. If T does not contain F, the result is T.
    if feature not in feature_model.get_features():
        return feature_model
    feature_to_delete = feature
    # Step 2. Let the parent feature of F be P.
    parent = feature_to_delete.get_parent()  
    # Step 3. If P is a MandOpt feature and F is a mandatory subfeature of P, 
    # GOTO step 4 with P instead of F.
    while feature_to_delete != feature_model.root and not parent.is_group() and feature_to_delete.is_mandatory():
        feature_to_delete = parent
        parent = feature_to_delete.get_parent()
    # If F is the root of T, the result is NIL.
    if feature_to_delete == feature_model.root:  
        return None
    # If P is a MandOpt feature and F is an optional subfeature of P, delete F.
    elif not parent.is_group() and feature_to_delete.is_optional():
        rel = next((r for r in parent.get_relations() if feature_to_delete in r.children), None)
        parent.get_relations().remove(rel)
    # If P is an Xor feature or an Or feature, delete F; if P has only one remaining subfeature, 
    # make P a MandOpt feature and its subfeature a mandatory subfeature.
    elif parent.is_alternative_group() or parent.is_or_group():
        rel = parent.get_relations()[0]
        rel.children.remove(feature_to_delete)
        if rel.card_max > 1:
            rel.card_max -= 1
    return feature_model


def transform_tree(functions: list[Callable], fm: FeatureModel, features: list[str], copy_tree: bool) -> FeatureModel:
    """Apply a list of functions (commitment_feature or deletion_feature) 
    to the tree of the feature model. 
    
    For each function, it uses each feature (in order) in the provided list as argument.
    """
    if copy_tree:
        tree = FeatureModel(copy.deepcopy(fm.root), fm.get_constraints())
    else:
        tree = fm
    for func, feature in zip(functions, features):
        if tree is not None:
            tree = func(tree, feature)
    return tree


def get_new_feature_name(fm: FeatureModel, prefix_name: str) -> str:
    """Return a new name for a feature (based on the provided prefix) that is not already in the feature model."""
    count = 1
    new_name = f'{prefix_name}'
    while fm.get_feature_by_name(new_name) is not None:
        new_name = f'{prefix_name}{count}'
        count += 1
    return new_name


def get_trees_from_original_root(fm: FeatureModel) -> list[FeatureModel]:
    """Given a feature model with non-unique features, 
    returns the subtrees the root of which are the original root of the feature model.
    
    The original root of the feature model is the most top feature 
    that is not a XOR group with two or more identical children.
    """
    root = fm.root
    if root.is_alternative_group():
        child_name = root.get_children()[0].name
        if all(child.name == child_name for child in root.get_children()):
            trees = []
            for child in root.get_children():
                subtrees = get_trees_from_original_root(FeatureModel(child, fm.get_constraints()))
                trees.extend(subtrees)
            return trees
    return [fm]