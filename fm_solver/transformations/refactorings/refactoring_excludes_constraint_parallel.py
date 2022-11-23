import multiprocessing

from flamapy.metamodels.fm_metamodel.models import FeatureModel, Feature, Relation, Constraint

from fm_solver.transformations.refactorings import RefactoringExcludesConstraint
from fm_solver.utils import fm_utils, constraints_utils


class RefactoringExcludesConstraintParallel(RefactoringExcludesConstraint):

    @staticmethod
    def transform(model: FeatureModel, instance: Constraint) -> FeatureModel:
        return eliminate_excludes_parallel(model, instance)


def eliminate_excludes_parallel(fm: FeatureModel, excludes_ctc: Constraint) -> FeatureModel:
    """Algorithm to eliminate a constraint 'A excludes B' from the feature model.
    
    The algorithm construct a feature model T whose products are those products of T 
    which do not contain both A and B.
    This set of products is the union of the products sets of T(-B) and T(-A+B).
    The product sets of T(-B) and T(-A+B) are disjoint. So the required feature model can be
    obtained by taking a new Xor feature as root which has T(-B) and T(-A+B) as subfeatures.
    """
    fm.get_constraints().remove(excludes_ctc)
    feature_name_a, feature_name_b = constraints_utils.left_right_features_from_simple_constraint(excludes_ctc)
    subtrees = fm_utils.get_trees_from_original_root(fm)
    #print(f'  |-#Subtrees: {len(subtrees)}:  #Features(mean): {statistics.mean([len(st.get_features()) for st in subtrees])}')
    trees_less = set()
    trees_lessplus = set()
    # Parallel code
    trees_lessB = []
    trees_lessA_plusB = []
    with multiprocessing.Pool() as pool: 
        # Construct T(-B)
        for tree in subtrees:
           trees_lessB.append(pool.apply_async(fm_utils.transform_tree, ([fm_utils.deletion_feature], tree, [feature_name_b], False)))
        # Construct T(-A+B)
        for tree in subtrees:
            trees_lessA_plusB.append(pool.apply_async(fm_utils.transform_tree, ([fm_utils.deletion_feature, fm_utils.commitment_feature], tree, [feature_name_a, feature_name_b], False)))

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
    new_root = Feature(fm_utils.get_new_feature_name(fm, 'root'), is_abstract=True)
    children = []
    for tree in trees_less.union(trees_lessplus):
        tree.root.parent = new_root
        children.append(tree.root)
    if not children:
        return None
    xor_rel = Relation(new_root, children, 1, 1)
    new_root.add_relation(xor_rel)
    return FeatureModel(new_root, fm.get_constraints())
