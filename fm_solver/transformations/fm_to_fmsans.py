import copy

from flamapy.core.transformations import ModelToModel
from flamapy.metamodels.fm_metamodel.models import FeatureModel, Constraint

from fm_solver.models import FMSans, fm_sans
from fm_solver.utils import utils, fm_utils
from fm_solver.transformations.refactorings import (
    RefactoringPseudoComplexConstraint,
    RefactoringStrictComplexConstraint
)


class FMToFMSans(ModelToModel):
    """Transform a feature model with cross-tree constraints to an equivalent
    feature model sans constraints (without any cross-tree constraints).
    
    The resulting feature model has the same semantics (i.e., same products) and 
    the same number of configurations.
    """

    @staticmethod
    def get_source_extension() -> str:
        return 'fm'

    @staticmethod
    def get_destination_extension() -> str:
        return 'fmsans'

    def __init__(self, source_model: FeatureModel) -> None:
        self._fm = source_model
    
    def transform(self) -> FMSans:
        return fm_to_fmsans(self._fm)


def fm_to_fmsans(fm: FeatureModel) -> FMSans:
    if not fm.get_constraints():
        # The feature model has not any constraint.
        return FMSans(None, fm, None, None)

    # Refactor pseudo-complex constraints
    fm = utils.apply_refactoring(fm, RefactoringPseudoComplexConstraint)
    # Refactor strict-complex constraints
    fm = utils.apply_refactoring(fm, RefactoringStrictComplexConstraint)
    
    # Get optimum constraints order
    constraints_order = analysis_constraints_order(fm)
    assert len(constraints_order[0]) == len(fm.get_constraints())

    # Split the feature model into two
    subtree_with_constraints_implications, subtree_without_constraints_implications = fm_utils.get_subtrees_constraints_implications(fm)
    print(f'Subtree without constraints implications: {subtree_without_constraints_implications}')
    #print(f'constraints_order: {constraints_order}')
    transformations_vector = fm_sans.get_transformations_vector(constraints_order)

    n_bits = len(transformations_vector)
    #binary_vector = format(0, f'0{n_bits}b')
    num = 0
    i_bit = n_bits
    max = 2**n_bits
    valid_transformed_numbers_trees = []
    percentage = 0.0
    while num < max:
        #binary_vector = list(format(num, f'0{n_bits}b')[::-1])
        binary_vector = list(format(num, f'0{n_bits}b'))
        tree, null_bit = fm_sans.execute_transformations_vector(subtree_with_constraints_implications, transformations_vector, binary_vector)
        if tree is not None:
            #print(f'{num}: {"".join(binary_vector)} -> OK')
            valid_transformed_numbers_trees.append(num)
            num += 1
        else:  # tree is None
            print(f'Transformation resulted in NULL. Bit: {null_bit}')
            num = fm_sans.get_next_number_prunning_binary_vector(binary_vector, null_bit)
            #print(f'  |- next number: {num}')
        percentage = (num / max) * 100
        print(f'#Valid subtrees: {len(valid_transformed_numbers_trees)}. Num: {num} / {max} Ratio: ({percentage}%)')
    
    result_fm = FMSans(subtree_with_constraints_implications=subtree_with_constraints_implications, 
                       subtree_without_constraints_implications=subtree_without_constraints_implications,
                       transformations_vector=transformations_vector,
                       transformations_ids=valid_transformed_numbers_trees)
    return result_fm


def analysis_constraints_order(fm: FeatureModel) -> tuple[list[Constraint], dict[int, tuple[int, int]]]:
    """It analyses and returns the best order in which the constrainst will be eliminated.  
    
    It applies an Greedy heuristic, based on the transformations that first reach 
    a NIL (None or Null) feature model.

    The result is a tuple with:
     - The list of constraints in order.
     - A dictionary of 'index -> (T0, T1)',
        where index is the index of the constraint in the previous list,
        and T0 and T1 are the two transformations of each constraint,
            where T0 will be codified with a bit to 0, and T1 will be codified with a bit to 1.
        T0 and T1 are also in order based on the transformation that first reaches a NIL model.
    """
    constraints = [ctc for ctc in fm.get_constraints()]
    best_constraints_order = []
    best_constraints_transformation_order = {}
    tree = FeatureModel(copy.deepcopy(fm.root))
    size = len(fm.get_constraints())
    i = 0
    while i < size and tree is not None:
        ctcs_ordered = analysis_constraints_order_estimation(tree, constraints)
        # Get the first transformation (only for the first one, i.e., the best one)
        first_ctc_transformation_order = ([ctcs_ordered[0][0]], {0: ctcs_ordered[1][0]})
        #print(f'first_ctc_transformation_order: {first_ctc_transformation_order}')
        transformation_vector = fm_sans.get_transformations_vector(first_ctc_transformation_order)
        # Execute the transformation
        tree = transformation_vector[0][0].transforms(tree)
        constraints.remove(ctcs_ordered[0][0])
        # Update the best order for the constraints
        best_constraints_order.append(ctcs_ordered[0][0])
        best_constraints_transformation_order[i] = ctcs_ordered[1][0]
        i += 1
    if tree is None:
        ctcs_ordered = analysis_constraints_order_estimation(fm, constraints)
        for k in range(i, size):
            index = k - i
            best_constraints_order.append(ctcs_ordered[0][index])
            best_constraints_transformation_order[k] = ctcs_ordered[1][index]
    return (best_constraints_order, best_constraints_transformation_order)


def analysis_constraints_order_estimation(fm: FeatureModel, constraints: list[Constraint]) -> tuple[list[Constraint], dict[int, tuple[int, int]]]:
    """Return a new order for the constraints based on a pre-analysis that takes into account
    the number of features to be removed by the transformations required to refactor the
    constraint without executing the transformation over the model.
    
    The result is a tuple with the list of constraints in order, and a dictionary with the index
    of the constraints and a tuple of (0,1) or (1,0) indicating the transformation that corresponds
    with the first transformation or the second transformation.
    0 is the first transformation; 1 is the second one.
    """
    #print(f'#Constraints: {len(constraints)}')
    #print(f'  |-#Requires: {len([ctc for ctc in constraints if constraints_utils.is_requires_constraint(ctc)])}')
    #print(f'  |-#Excludes: {len([ctc for ctc in constraints if constraints_utils.is_excludes_constraint(ctc)])}')

    # Order of the constraints:
    constraints = constraints
    constraints_analysis = {}
    for i, ctc in enumerate(constraints):
        constraints_analysis[i] = fm_utils.numbers_of_features_to_be_removed(fm, ctc)
    # Order by best transformation
    constraints_ordered = dict(sorted(constraints_analysis.items(), key=lambda item: max(item[1][0], item[1][1]), reverse=True))  
    constraints_ordered_transformations = {}
    for i, (key, value) in enumerate(constraints_ordered.items()):
        constraints_ordered_transformations[i] = (0, 1) if value[0] >= value[1] else (1, 0)
    new_constraints_ordered = [constraints[i] for i in constraints_ordered.keys()]
    #print(f'new_constraints_ordered: {[ctc.ast.pretty_str() for ctc in new_constraints_ordered]}')
    #print(f'constraints_ordered_transformations: {constraints_ordered_transformations}')
    # for i in range(new_constraints_ordered):
    #     print(f'CTC {i}: {new_constraints_ordered[i].ast.to_pretty_str()}, {(constraints_ordered[i][0], constraints_ordered[i][1]), ({(constraints_ordered_transformations[i][0], constraints_ordered_transformations[i][1])})}')
    return (new_constraints_ordered, constraints_ordered_transformations)



