"""
This module contains all utils related to the management of a feature model.
"""

import copy
from collections.abc import Callable

from flamapy.metamodels.fm_metamodel.models import (
    FeatureModel,
    Feature, 
    Relation, 
    Constraint, 
    Attribute
)

from fm_solver.models.feature_model import FM
from fm_solver.utils import constraints_utils


def commitment_feature(feature_model: FM, feature_name: str) -> FM:
    return feature_model.commit_feature(feature_name)


def deletion_feature(feature_model: FM, feature_name: str) -> FM:
    return feature_model.delete_feature(feature_name)


def transform_tree(functions: list[Callable], fm: FM, features: list[str], copy_tree: bool, features_already_executed: tuple[set[str], set[str]]) -> FM:
    """Apply a list of functions (commitment_feature or deletion_feature) 
    to the tree of the feature model. 
    
    For each function, it uses each feature (in order) in the provided list as argument.
    """
    if copy_tree:
        tree = FM(copy.deepcopy(fm.root), fm.get_constraints())
    else:
        tree = fm
    for func, feature in zip(functions, features):
        if tree is not None:
            tree = func(tree, feature, features_already_executed)
    return tree


def get_new_feature_name(fm: FM, prefix_name: str) -> str:
    """Return a new name for a feature (based on the provided prefix) that is not already in the feature model."""
    count = 1
    new_name = f'{prefix_name}'
    while fm.get_feature_by_name(new_name) is not None:
        new_name = f'{prefix_name}{count}'
        count += 1
    return new_name


def get_trees_from_original_root(fm: FM) -> list[FM]:
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
                subtrees = get_trees_from_original_root(FM(child, fm.get_constraints()))
                trees.extend(subtrees)
            return trees
    return [fm]


def get_model_from_subtrees(fm: FM, subtrees: set[FM]) -> FeatureModel:
    """It returns a new feature model by joining all exclusive subtrees with a XOR group.
    
    The result is a model with a new root, which is an XOR group where each subfeatures is one
    of the subtrees.
    """
    new_root = Feature(get_new_feature_name(fm, 'XOR_Root'), is_abstract=True)
    add_auxiliary_feature_attribute(new_root)
    fm.add_feature(new_root)
    #new_root.add_attribute(Attribute(name='new', domain=None, default_value=None, null_value=None))
    #new_root = Feature(fm.root.name, is_abstract=True)  # We may use the same feature's name root.
    children = []
    for tree in subtrees:
        tree.root.parent = new_root
        children.append(tree.root)
    if not children:
        return None
    xor_rel = Relation(new_root, children, 1, 1)
    new_root.add_relation(xor_rel)
    return FeatureModel(new_root)


def numbers_of_features_to_be_removed(fm: FM, ctc: Constraint) -> tuple[int, int]:
    """Return the number of features that will be deleted from the feature model when
    the given constraint is refactored into the tree diagram.
    
    It returns a tuple where the first value corresponds with the first transformation required
    to eliminate the CTC (i.e., the commitment or deletion of a feature), while the second value
    corresponds with the second transformation required to eliminate the CTC (i.e., the 
    deletion of both features or the deletion of the first feature and the commitment of the other.
    """
    left_feature, right_feature = constraints_utils.left_right_features_from_simple_constraint(ctc)
    if constraints_utils.is_requires_constraint(ctc):
        t_0 = numbers_of_features_to_be_removed_commitment(fm, right_feature)
        t_1 = numbers_of_features_to_be_removed_deletion(fm, left_feature) + numbers_of_features_to_be_removed_deletion(fm, right_feature)
    else:  # it is an excludes
        t_0 = numbers_of_features_to_be_removed_deletion(fm, right_feature)
        t_1 = numbers_of_features_to_be_removed_deletion(fm, left_feature) + numbers_of_features_to_be_removed_commitment(fm, right_feature)
    return (t_0, t_1)


def numbers_of_features_to_be_removed_commitment(fm: FM, feature_name: str) -> int:
    """Return the number of features that will be removed from the feature model when
    the given feature is commitment into the diagram."""
    feature = fm.get_feature_by_name(feature_name)
    if feature not in fm.get_features():
        return len(fm.get_features())
    feature_to_commit = feature
    n_features = 0
    while feature_to_commit != fm.root:
        parent = feature_to_commit.get_parent()
        if parent.is_alternative_group():  
            n_features += len(parent.get_relations()[0].children) - 1
            for child in parent.get_relations()[0].children:
                if child != feature_to_commit:
                    n_features += children_number(child)
        feature_to_commit = parent
    return n_features


def numbers_of_features_to_be_removed_deletion(fm: FM, feature_name: str) -> int:
    """Return the number of features that will be removed from the feature model when
    the given feature is deleted from the diagram."""
    feature = fm.get_feature_by_name(feature_name)
    if feature not in fm.get_features():
        return 0
    n_features = 0
    feature_to_delete = feature
    parent = feature_to_delete.get_parent()  
    while feature_to_delete != fm.root and not parent.is_group() and feature_to_delete.is_mandatory():
        feature_to_delete = parent
        parent = feature_to_delete.get_parent()
    if feature_to_delete == fm.root:
        n_features = len(fm.get_features())
    elif not parent.is_group() and feature_to_delete.is_optional():
        n_features = 1 + children_number(feature_to_delete)
    elif parent.is_alternative_group() or parent.is_or_group():
        n_features = 1 + children_number(feature_to_delete)
    return n_features


def children_number(feature: Feature) -> int:
    """Return the number of children in all the subtrees of the given feature."""
    if feature is None:
        return 0
    n_features = len(feature.get_children())
    for child in feature.get_children():
        n_features += children_number(child)
    return n_features


def get_subtrees_constraints_implications(fm: FM) -> tuple[FM, FM]:
    """Return the subtree of the feature model that is affected by cross-tree constraints,
    and the subtree of the feature model that is not affected by any cross-tree constraint."""
    subtree_without_implications = get_subtree_without_constraints_implications(fm)
    if subtree_without_implications is None:
        subtree = FM(copy.deepcopy(fm.root))
        return (subtree, None)
    features = subtree_without_implications.get_features()
    features.remove(subtree_without_implications.root)
    subtree = FM(copy.deepcopy(fm.root))
    for f in features:
        feature = subtree.get_feature_by_name(f.name)
        subtree = remove_feature_branch(subtree, feature)
    return (subtree, subtree_without_implications)


def get_subtree_without_constraints_implications(fm: FM) -> FM:
    """Return the subtree of the feature model that is not affected by any constraint."""
    if len(fm.get_constraints()) == 0:
        return None
    if len(fm.root.get_relations()) < 2:
        return None
    subtree = FM(copy.deepcopy(fm.root))
    for ctc in fm.get_constraints():
        for f in ctc.get_features():
            if subtree is not None:
                feature = subtree.get_feature_by_name(f)
                subtree = remove_feature_branch(subtree, feature)
    if subtree is None or len(subtree.get_features()) == 1:
        subtree = None
    return subtree


def remove_feature_branch(fm: FM, feature: Feature) -> FM:
    """Remove the entire branch from the root that containts the given feature."""
    if feature == fm.root:
        return None
    parent = feature.get_parent() if feature is not None else None
    while feature is not None and parent != fm.root:
        feature = parent
        parent = feature.get_parent()
    if feature is not None:
        relations_to_be_deleted = [rel for rel in parent.get_relations() if feature in rel.children]
        for rel in relations_to_be_deleted:
            parent.get_relations().remove(rel)
            for f in rel.children:
                fm.delete_feature(f)
    return fm


def remove_leaf_abstract_auxiliary_features(model: FM) -> FM:
    """Remove all leaf abstract features from the feature model."""
    assert len(model.get_constraints()) == 0
    
    is_there_leaf_abstract_aux_features = False
    features = list(model.get_features())
    for feature in features:
        if feature.is_leaf() and feature.is_abstract and is_auxiliary_feature(feature):
            is_there_leaf_abstract_aux_features = True
            parent = feature.get_parent()
            # If parent is not group we eliminate the relation
            if not parent.is_group():
                rel = next((r for r in parent.get_relations() if feature in r.children), None)
                parent.get_relations().remove(rel)
                model._delete_feature_branch(feature)
                #for f in rel.children:
                #    model._delete_feature_branch(f)
            # If parent is group we eliminate the feature from the group relation
            else:
                rel = parent.get_relations()[0]
                rel.children.remove(feature)
                model._delete_feature_branch(feature)
                if rel.card_max > 1:
                    rel.card_max -= 1
    if is_there_leaf_abstract_aux_features:  # need recursion
        model = remove_leaf_abstract_auxiliary_features(model)
    return model


def to_unique_features(model: FM) -> FM:
    """Replace duplicated features names in the feature model.
    
    The model is augmented with attributes with features' references to the original features.
    """
    unique_features_names = set()
    for feature in model.get_features():
        if feature.name not in unique_features_names:
            unique_features_names.add(feature.name)
        else:
            new_name = get_new_feature_name(model, feature.name)
            attribute = Attribute('ref', None, feature.name, None)
            attribute.set_parent(feature)
            feature.add_attribute(attribute)
            feature.name = new_name
            unique_features_names.add(feature.name)
    return model


def get_unique_features(model: FeatureModel) -> list[Feature]:
    unique_features = []
    unique_features_names = set()
    for feature in model.get_features():
        if feature.name not in unique_features_names:
            unique_features_names.add(feature.name)
            unique_features.append(feature)
    return unique_features


def fm_stats(fm: FeatureModel) -> str:
    lines = []
    n_features = len(fm.get_features())
    n_unique_features = len(set(fm.get_features()))
    n_abstract_features = sum(f.is_abstract for f in fm.get_features())
    n_concrete_features = n_features - n_abstract_features
    n_auxiliary_features = sum(is_auxiliary_feature(f) for f in fm.get_features())
    n_ctcs = len(fm.get_constraints())
    n_ctcs_simple = sum(constraints_utils.is_simple_constraint(ctc) for ctc in fm.get_constraints())
    n_ctcs_complex = n_ctcs - n_ctcs_simple
    n_pseudo_ctcs = sum(constraints_utils.is_pseudo_complex_constraint(ctc) for ctc in fm.get_constraints())
    n_strict_ctcs = n_ctcs_complex - n_pseudo_ctcs
    n_requires_ctcs = sum(constraints_utils.is_requires_constraint(ctc) for ctc in fm.get_constraints())
    n_excludes_ctcs = n_ctcs_simple - n_requires_ctcs

    lines.append(f'FM stats:')
    lines.append(f'  #Features:            {n_features}')
    lines.append(f'    #Concrete features: {n_concrete_features}')
    lines.append(f'    #Abstract features: {n_abstract_features}')
    lines.append(f'    #Auxiliary features:{n_auxiliary_features}')
    lines.append(f'    #Unique features:   {n_unique_features}')
    lines.append(f'  #Constraints:         {n_ctcs}')
    lines.append(f'    #Simple CTCs:       {n_ctcs_simple}')
    lines.append(f'      #Requires:        {n_requires_ctcs}')
    lines.append(f'      #Excludes:        {n_excludes_ctcs}')
    lines.append(f'    #Complex CTCs:      {n_ctcs_complex}')
    lines.append(f'      #Pseudo CTCs:     {n_pseudo_ctcs}')
    lines.append(f'      #Strict CTCs:     {n_strict_ctcs}')
    return '\n'.join(lines)


def add_auxiliary_feature_attribute(feature: Feature) -> Feature:
    aux_attribute = Attribute(name=FM.AUXILIARY_FEATURES_ATTRIBUTE, domain=None, default_value=None, null_value=None)
    aux_attribute.set_parent(feature)
    feature.add_attribute(aux_attribute)
    return feature 


def is_auxiliary_feature(feature: Feature) -> bool:
    return any(a for a in feature.get_attributes() if a.name == FM.AUXILIARY_FEATURES_ATTRIBUTE)
    