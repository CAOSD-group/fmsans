from flamapy.core.transformations import ModelToModel
from flamapy.metamodels.fm_metamodel.models import FeatureModel, Constraint

from fm_solver.models.feature_model import FM
from fm_solver.models import FMSans, fm_sans
from fm_solver.models.utils import TransformationsVector
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

    def __init__(self, source_model: FeatureModel, n_cores: int, n_tasks: int, current_task: int, n_min: int,n_max: int,min_time:int,max_time:int) -> None:
         self.feature_model = source_model
         self.n_cores = n_cores
         self.n_tasks = n_tasks
         self.current_task = current_task
         self.n_min_job = n_min
         self.n_max_job = n_max
         self.min_time = min_time
         self.max_time = max_time

    def transform(self) -> FMSans:
         return fm_to_fmsans(self.feature_model, self.n_cores, self.n_tasks, self.current_task, self.n_min_job,self.n_max_job,self.min_time,self.max_time)


def fm_to_fmsans(feature_model: FeatureModel, n_cores: int = 1, n_tasks: int = 1, current_task: int = 0, n_min_job:int=-1,n_max_job:int=-1,min_time:int=-1,max_time:int=-1) -> FMSans:
    fm = FM.from_feature_model(feature_model)

    if not fm.get_constraints():
        # The feature model has not any constraint.
        return FMSans(FM(fm.root), None, {})

    # Refactor pseudo-complex constraints
    fm = utils.apply_refactoring(fm, RefactoringPseudoComplexConstraint)
    # Refactor strict-complex constraints
    fm = utils.apply_refactoring(fm, RefactoringStrictComplexConstraint)

    # Get transformations vector
    trans_vector = TransformationsVector.from_constraints(fm.get_constraints())
    
    # Get valid transformations ids.
    n_bits = trans_vector.n_bits()
    n_processes  = n_cores if n_bits > n_cores else 1
    valid_transformed_numbers_trees = trans_vector.get_valid_transformations_ids(fm, n_processes, n_tasks, current_task, n_min_job,n_max_job, min_time,max_time)
    
    # Get FMSans instance
    return FMSans(FM(fm.root), trans_vector, valid_transformed_numbers_trees)


### The following is an optimization.

def get_optimum_constraints_order(fm: FeatureModel) -> tuple[list[Constraint], dict[int, tuple[int, int]]]:
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
    #tree = FeatureModel(copy.deepcopy(fm.root))  # This is needed.
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
