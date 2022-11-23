import statistics
import multiprocessing
import copy
from typing import Any
from collections.abc import Callable
import datetime

from flamapy.core.models import AST, ASTOperation, ast
from flamapy.metamodels.fm_metamodel.models import FeatureModel, Feature, Constraint, Relation


def is_simple_constraint(constraint: Constraint) -> bool:
    """Return true if the constraint is a simple constraint (requires or excludes)."""
    return is_requires_constraint(constraint) or is_excludes_constraint(constraint)


def is_complex_constraint(constraint: Constraint) -> bool:
    """Return true if the constraint is a complex constraint (i.e., it is not a simple constraint)."""
    return not is_simple_constraint(constraint)


def is_requires_constraint(constraint: Constraint) -> bool:
    """Return true if the constraint is a requires constraint."""
    root_op = constraint.ast.root
    if root_op.is_binary_op():
        if root_op.data in [ASTOperation.REQUIRES, ASTOperation.IMPLIES]:
            return root_op.left.is_term() and root_op.right.is_term()
        elif root_op.data == ASTOperation.OR:
            neg_left = root_op.left.data == ASTOperation.NOT and root_op.left.left.is_term()
            neg_right = root_op.right.data == ASTOperation.NOT and root_op.right.left.is_term()
            return neg_left and root_op.right.is_term() or neg_right and root_op.left.is_term()
    return False


def is_excludes_constraint(constraint: Constraint) -> bool:
    """Return true if the constraint is an excludes constraint."""
    root_op = constraint.ast.root
    if root_op.is_binary_op():
        if root_op.data in [ASTOperation.EXCLUDES, ASTOperation.XOR]:
            return root_op.left.is_term() and root_op.right.is_term()
        elif root_op.data in [ASTOperation.REQUIRES, ASTOperation.IMPLIES]:
            neg_right = root_op.right.data == ASTOperation.NOT and root_op.right.left.is_term()
            return root_op.left.is_term() and neg_right
        elif root_op.data == ASTOperation.OR:
            neg_left = root_op.left.data == ASTOperation.NOT and root_op.left.left.is_term()
            neg_right = root_op.right.data == ASTOperation.NOT and root_op.right.left.is_term()
            return neg_left and neg_right
    return False


def get_new_ctc_name(ctcs_names: list[str], prefix_name: str) -> str:
    """Return a new name for a constraint (based on the provided prefix) that is not already in the given list of constraints' names."""
    count = 1
    new_name = f'{prefix_name}'
    while new_name in ctcs_names:
        new_name = f'{prefix_name}{count}'
        count += 1
    return new_name


####################################################################################################
def filter_products(fm: FeatureModel, configurations: list[list[str]]) -> list[list[str]]:
    """Given a list of configurations return it with the configurations filtered.
    
    This method takes into account that the features in the FM can be not unique. 
    That is, features can have its corresponding features in a dictionary
    indicating that the feature is non-unique and appears in other part of the FM.
    The corresponding value in the dictionary points to the original feature.

    The filters performed are the following:
      a) Remove abstract features.
      b) Substitute non-unique features with the original one.
      c) Remove duplicate features.
    """
    filtered_configs = set()
    for config in configurations:
        c = set()
        for f in config:
            feature = fm.get_feature_by_name(f)
            if not feature.is_abstract:
                original_feature_name = get_original_feature_from_duplicates(f, fm.get_features())
                c.add(original_feature_name)
        filtered_configs.add(frozenset(c))
    return filtered_configs


def get_original_feature_from_duplicates(feature_name: str, features: list[Feature]) -> str:
    names = [f.name for f in features if f.name.startswith(feature_name) or feature_name.startswith(f.name)]
    names.sort(key=len)
    return names[0]

def remove_references(fm: FeatureModel) -> FeatureModel:
    """Given a feature model with a references dictionary, 
    substitute each reference with the original feature 
    giving as result a feature model with non-unique features."""
    if hasattr(fm, 'dict_references'):    
        for feature in fm.get_features():
            if feature.name in fm.dict_references.keys():
                feature = fm.dict_references[feature.name]
    return fm


def update_feature(fm: FeatureModel, 
                   feature_old_name: str, 
                   feature_new_name: str, 
                   feature_type: str, 
                   group_card_min: int, 
                   group_card_max: int, 
                   feature_attributes: list[dict[str, str]]) -> FeatureModel:
    
    return fm


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


def construct_plusB(fm: FeatureModel, feature_name_b: str) -> FeatureModel:
    tree = FeatureModel(copy.deepcopy(fm.root))
    return commitment_feature(tree, feature_name_b)


def construct_lessB(fm: FeatureModel, feature_name_b: str) -> FeatureModel:
    tree = FeatureModel(copy.deepcopy(fm.root))
    return deletion_feature(tree, feature_name_b)


def construct_lessA_lessB(fm: FeatureModel, feature_name_a: str, feature_name_b: str) -> FeatureModel:
    tree = FeatureModel(copy.deepcopy(fm.root))
    tree = deletion_feature(tree, feature_name_a)
    if tree is not None:
        tree = deletion_feature(tree, feature_name_b)
    return tree


def construct_lessA_plusB(fm: FeatureModel, feature_name_a: str, feature_name_b: str) -> FeatureModel:
    tree = FeatureModel(copy.deepcopy(fm.root))
    tree = deletion_feature(tree, feature_name_a)
    if tree is not None:
        tree = commitment_feature(tree, feature_name_b)
    return tree


def eliminate_requires(fm: FeatureModel, requires_ctc: Constraint) -> FeatureModel:
    """Algorithm to eliminate a constraint 'A requires B' from the feature model.
    
    The algorithm construct a feature model T whose products are those products of T 
    which contain B when they contain A.
    This set of products is the union of the products sets of T(+B) and T(-A-B).
    The product sets of T(+B) and T(-A-B) are disjoint. So the required feature model can be
    obtained by taking a new Xor feature as root which has T(+B) and T(-A-B) as subfeatures.
    """
    fm.get_constraints().remove(requires_ctc)
    feature_name_a, feature_name_b = left_right_features_names_from_simple_constraint(requires_ctc)
    subtrees = get_trees_from_original_root(fm)
    print(f'  |-#Subtrees: {len(subtrees)}:  #Features(mean): {statistics.mean([len(st.get_features()) for st in subtrees])}')
    trees_plus = set()
    trees_less = set()
    #original_tree = pickle.dumps(fm.root, protocol=pickle.HIGHEST_PROTOCOL)
    # Construct T(+B)   
    for tree in subtrees:
        t_plus = transform_tree([commitment_feature], tree, [feature_name_b], True)
        if t_plus is not None:
            trees_plus.add(t_plus)
    # Construct T(-A-B)
    for tree in subtrees:
        t_less = transform_tree([deletion_feature, deletion_feature], tree, [feature_name_a, feature_name_b], False)
        if t_less is not None:
            trees_less.add(t_less)

    # The result consists of a new root, which is an Xor feature,
    # with subfeatures T(+B) and T(-A-B).
    new_root = Feature(get_new_feature_name(fm, 'root'), is_abstract=True)
    children = []
    for tree in trees_plus.union(trees_less):
        tree.root.parent = new_root
        children.append(tree.root)
    if not children:
        return None
    xor_rel = Relation(new_root, children, 1, 1)
    new_root.add_relation(xor_rel)
    return FeatureModel(new_root, fm.get_constraints())


def eliminate_excludes(fm: FeatureModel, excludes_ctc: Constraint) -> FeatureModel:
    """Algorithm to eliminate a constraint 'A excludes B' from the feature model.
    
    The algorithm construct a feature model T whose products are those products of T 
    which do not contain both A and B.
    This set of products is the union of the products sets of T(-B) and T(-A+B).
    The product sets of T(-B) and T(-A+B) are disjoint. So the required feature model can be
    obtained by taking a new Xor feature as root which has T(-B) and T(-A+B) as subfeatures.
    """
    fm.get_constraints().remove(excludes_ctc)
    feature_name_a, feature_name_b = left_right_features_names_from_simple_constraint(excludes_ctc)
    subtrees = get_trees_from_original_root(fm)
    print(f'  |-#Subtrees: {len(subtrees)}:  #Features(mean): {statistics.mean([len(st.get_features()) for st in subtrees])}')
    trees_less = set()
    trees_lessplus = set()
    # Construct T(-B)
    for tree in subtrees:
        t_less = transform_tree([deletion_feature], tree, [feature_name_b], True)
        if t_less is not None:
            trees_less.add(t_less)
    # Construct T(-A+B)
    for tree in subtrees:
        t_lessplus = transform_tree([deletion_feature, commitment_feature], tree, [feature_name_a, feature_name_b], False)
        if t_lessplus is not None:
            trees_lessplus.add(t_lessplus)

    # The result consists of a new root, which is an Xor feature,
    # with subfeatures T(-B) and T(-A+B).
    new_root = Feature(get_new_feature_name(fm, 'root'), is_abstract=True)
    children = []
    for tree in trees_less.union(trees_lessplus):
        tree.root.parent = new_root
        children.append(tree.root)
    if not children:
        return None
    xor_rel = Relation(new_root, children, 1, 1)
    new_root.add_relation(xor_rel)
    return FeatureModel(new_root, fm.get_constraints())


def left_right_features_names_from_simple_constraint(simple_ctc: Constraint) -> tuple[str, str]:
    """Return the names of the features involved in a simple constraint.
    
    A simple constraint can be a requires constraint or an excludes constraint.
    A requires constraint can be represented in the AST of the constraint with one of the following structures:
        A requires B
        A => B
        !A v B
    An excludes constraint can be represented in the AST of the constraint with one of the following structures:
        A excludes B
        A => !B
        !A v !B
    """
    assert is_simple_constraint(simple_ctc)

    root_op = simple_ctc.ast.root
    if root_op.data in [ASTOperation.REQUIRES, ASTOperation.IMPLIES, ASTOperation.EXCLUDES]:
        left = root_op.left.data
        right = root_op.right.data
        if right == ASTOperation.NOT:
            right = root_op.right.left.data
    elif root_op.data == ASTOperation.OR:
        left = root_op.left.data
        right = root_op.right.data
        if left == ASTOperation.NOT and right == ASTOperation.NOT:  # excludes
            left = root_op.left.left.data
            right = root_op.right.left.data
        elif left == ASTOperation.NOT:  # implies: A -> B
            left = root_op.left.left.data
            right = root_op.right.data
        elif right == ASTOperation.NOT:  # implies: B -> A
            left = root_op.right.left.data
            right = root_op.left.data
    return (left, right)


def get_new_feature_name(fm: FeatureModel, prefix_name: str) -> str:
    """Return a new name for a feature based on the provided prefix."""
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
    that is not a XOR group with two identical children.
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


def to_unique_features(fm: FeatureModel) -> FeatureModel:
    """Replace duplicated features names."""
    if not hasattr(fm, 'dict_references'):
            fm.dict_references = {}
    unique_features_names = []
    for f in fm.get_features():
        if f.name not in unique_features_names:
            unique_features_names.append(f.name)
        else:
            new_name = get_new_feature_name(fm, f.name)
            fm.dict_references[new_name] = f.name
            f.name = new_name
            unique_features_names.append(f.name)
    return fm

def remove_leaf_abstract_features(model: FeatureModel) -> FeatureModel:
    assert len(model.get_constraints()) == 0
    
    for feature in model.get_features():
        if feature.is_leaf() and feature.is_abstract:
            parent = feature.get_parent()
            # If parent is not group we eliminate the relation
            if not parent.is_group():
                rel = next((r for r in parent.get_relations() if feature in r.children), None)
                parent.get_relations().remove(rel)
            # If parent is group we eliminate the feature from the group relation
            else:
                rel = parent.get_relations()[0]
                rel.children.remove(feature)
                if rel.card_max > 1:
                    rel.card_max -= 1
    abstract_features = len([f for f in model.get_features() if f.is_leaf() and f.is_abstract])
    if abstract_features > 0:
        model = remove_leaf_abstract_features(model)
    return model


def eliminate_requires_parallel(fm: FeatureModel, requires_ctc: Constraint) -> FeatureModel:
    """Algorithm to eliminate a constraint 'A requires B' from the feature model.
    
    The algorithm construct a feature model T whose products are those products of T 
    which contain B when they contain A.
    This set of products is the union of the products sets of T(+B) and T(-A-B).
    The product sets of T(+B) and T(-A-B) are disjoint. So the required feature model can be
    obtained by taking a new Xor feature as root which has T(+B) and T(-A-B) as subfeatures.
    """
    fm.get_constraints().remove(requires_ctc)
    feature_name_a, feature_name_b = left_right_features_names_from_simple_constraint(requires_ctc)
    subtrees = get_trees_from_original_root(fm)
    print(f'  |-#Subtrees: {len(subtrees)}:  #Features(mean): {statistics.mean([len(st.get_features()) for st in subtrees])}')
    trees_plus = set()
    trees_less = set()
    #original_tree = pickle.dumps(fm.root, protocol=pickle.HIGHEST_PROTOCOL)
    # Parallel code
    trees_plusB = []
    trees_lessA_lessB = []
    with multiprocessing.Pool() as pool: 
        # Construct T(+B)   
        for tree in subtrees:
            #tree_copy = FeatureModel(copy.deepcopy(tree.root))
            #tree_copy = FeatureModel(pickle.loads(original_tree))
            trees_plusB.append(pool.apply_async(transform_tree, ([commitment_feature], tree, [feature_name_b], False)))
            #trees_plusB.append(pool.apply_async(construct_plusB, (tree, feature_name_b)))
        # Construct T(-A-B)
        for tree in subtrees:
            #tree_copy = FeatureModel(copy.deepcopy(tree.root))
            #tree_copy = FeatureModel(pickle.loads(original_tree))
            trees_lessA_lessB.append(pool.apply_async(transform_tree, ([deletion_feature, deletion_feature], tree, [feature_name_a, feature_name_b], False)))
            #trees_lessA_lessB.append(pool.apply_async(construct_lessA_lessB, (tree, feature_name_a, feature_name_b)))

        for p in trees_plusB:
            p.wait()
        for p in trees_lessA_lessB:
            p.wait()

        for p in trees_plusB:
            t_plus = p.get()
            if t_plus is not None:
                trees_plus.add(t_plus)

        for p in trees_lessA_lessB:
            t_less = p.get()
            if t_less is not None:
                trees_less.add(t_less)

    # The result consists of a new root, which is an Xor feature,
    # with subfeatures T(+B) and T(-A-B).
    new_root = Feature(get_new_feature_name(fm, 'root'), is_abstract=True)
    children = []
    for tree in trees_plus.union(trees_less):
        tree.root.parent = new_root
        children.append(tree.root)
    if not children:
        return None
    xor_rel = Relation(new_root, children, 1, 1)
    new_root.add_relation(xor_rel)
    return FeatureModel(new_root, fm.get_constraints())


def eliminate_excludes_parallel(fm: FeatureModel, excludes_ctc: Constraint) -> FeatureModel:
    """Algorithm to eliminate a constraint 'A excludes B' from the feature model.
    
    The algorithm construct a feature model T whose products are those products of T 
    which do not contain both A and B.
    This set of products is the union of the products sets of T(-B) and T(-A+B).
    The product sets of T(-B) and T(-A+B) are disjoint. So the required feature model can be
    obtained by taking a new Xor feature as root which has T(-B) and T(-A+B) as subfeatures.
    """
    fm.get_constraints().remove(excludes_ctc)
    feature_name_a, feature_name_b = left_right_features_names_from_simple_constraint(excludes_ctc)
    subtrees = get_trees_from_original_root(fm)
    print(f'  |-#Subtrees: {len(subtrees)}:  #Features(mean): {statistics.mean([len(st.get_features()) for st in subtrees])}')
    trees_less = set()
    trees_lessplus = set()
    # Parallel code
    trees_lessB = []
    trees_lessA_plusB = []
    with multiprocessing.Pool() as pool: 
        # Construct T(-B)
        for tree in subtrees:
           trees_lessB.append(pool.apply_async(transform_tree, ([deletion_feature], tree, [feature_name_b], False)))
           #trees_lessB.append(pool.apply_async(construct_lessB, (tree, feature_name_b)))
        # Construct T(-A+B)
        for tree in subtrees:
            trees_lessA_plusB.append(pool.apply_async(transform_tree, ([deletion_feature, commitment_feature], tree, [feature_name_a, feature_name_b], False)))
            #trees_lessA_plusB.append(pool.apply_async(construct_lessA_plusB, (tree, feature_name_a, feature_name_b)))

        for p in trees_lessB:
            p.wait()
        for p in trees_lessA_plusB:
            p.wait()

        for p in trees_lessB:
            t_less = p.get()
            if t_less is not None:
                trees_less.add(t_less)

        for p in trees_lessA_plusB:
            t_lessplus = p.get()
            if t_lessplus is not None:
                trees_lessplus.add(t_lessplus)

    # The result consists of a new root, which is an Xor feature,
    # with subfeatures T(-B) and T(-A+B).
    new_root = Feature(get_new_feature_name(fm, 'root'), is_abstract=True)
    children = []
    for tree in trees_less.union(trees_lessplus):
        tree.root.parent = new_root
        children.append(tree.root)
    if not children:
        return None
    xor_rel = Relation(new_root, children, 1, 1)
    new_root.add_relation(xor_rel)
    return FeatureModel(new_root, fm.get_constraints())


def children_number(feature: Feature) -> int:
    """Return the number of children in all the subtrees of the given feature."""
    if feature is None:
        return 0
    n_features = len(feature.get_children())
    for child in feature.get_children():
        n_features += children_number(child)
    return n_features