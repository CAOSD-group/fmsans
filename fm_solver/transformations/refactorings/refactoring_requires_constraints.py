from flamapy.metamodels.fm_metamodel.models import FeatureModel, Feature, Relation, Constraint

from fm_solver.transformations.refactorings import FMRefactoring
from fm_solver.utils import fm_utils, constraints_utils


class RefactoringRequiresConstraint(FMRefactoring):

    @staticmethod
    def get_name() -> str:
        return 'Requires constraint refactoring'
    
    @staticmethod
    def get_description() -> str:
        return ("It translate a requires constraint from the feature model to the feature tree.")

    @staticmethod
    def get_language_construct_name() -> str:
        return 'Requires constraint'

    @staticmethod
    def get_instances(model: FeatureModel) -> list[Constraint]:
        return [ctc for ctc in model.get_constraints() 
                if constraints_utils.is_requires_constraint()]

    @staticmethod
    def is_applicable(model: FeatureModel) -> bool:
        return len(RefactoringRequiresConstraint.get_instances(model)) > 0

    @staticmethod
    def transform(model: FeatureModel, instance: Constraint) -> FeatureModel:
        return eliminate_requires(model, instance)


def eliminate_requires(fm: FeatureModel, requires_ctc: Constraint) -> FeatureModel:
    """Algorithm to eliminate a constraint 'A requires B' from the feature model.
    
    The algorithm construct a feature model T whose products are those products of T 
    which contain B when they contain A.
    This set of products is the union of the products sets of T(+B) and T(-A-B).
    The product sets of T(+B) and T(-A-B) are disjoint. So the required feature model can be
    obtained by taking a new Xor feature as root which has T(+B) and T(-A-B) as subfeatures.
    """
    fm.get_constraints().remove(requires_ctc)
    feature_name_a, feature_name_b = constraints_utils.left_right_features_from_simple_constraint(requires_ctc)
    subtrees = fm_utils.get_trees_from_original_root(fm)
    #print(f'  |-#Subtrees: {len(subtrees)}:  #Features(mean): {statistics.mean([len(st.get_features()) for st in subtrees])}')
    trees_plus = set()
    trees_less = set()
    # Construct T(+B)   
    for tree in subtrees:
        t_plus = fm_utils.transform_tree([fm_utils.commitment_feature], tree, [feature_name_b], True)
        if t_plus is not None:
            trees_plus.add(t_plus)
    # Construct T(-A-B)
    for tree in subtrees:
        t_less = fm_utils.transform_tree([fm_utils.deletion_feature, fm_utils.deletion_feature], tree, [feature_name_a, feature_name_b], False)
        if t_less is not None:
            trees_less.add(t_less)

    # The result consists of a new root, which is an Xor feature,
    # with subfeatures T(+B) and T(-A-B).
    new_root = Feature(fm_utils.get_new_feature_name(fm, 'root'), is_abstract=True)
    children = []
    for tree in trees_plus.union(trees_less):
        tree.root.parent = new_root
        children.append(tree.root)
    if not children:
        return None
    xor_rel = Relation(new_root, children, 1, 1)
    new_root.add_relation(xor_rel)
    return FeatureModel(new_root, fm.get_constraints())
