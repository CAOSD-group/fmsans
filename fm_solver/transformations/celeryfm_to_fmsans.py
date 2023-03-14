from flamapy.core.transformations import ModelToModel
from flamapy.metamodels.fm_metamodel.models import FeatureModel, Constraint
from fm_solver.models import feature_model

from fm_solver.models.feature_model import FM
from fm_solver.models import FMSans, fm_sans
from fm_solver.models.utils import TransformationsVector
from fm_solver.transformations.fm_to_fmsans import FMToFMSans
from fm_solver.utils import utils, fm_utils
from fm_solver.transformations.refactorings import (
    RefactoringPseudoComplexConstraint,
    RefactoringStrictComplexConstraint
)

import csv
from time import process_time

class CeleryFMToFMSans(FMToFMSans):
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

    def __init__(self, source_model: feature_model, n_min: int, n_current: int, n_max: int, division_id: int,divisions_max: int,t_max: int) -> None:
         super().__init__(source_model, 1, divisions_max, division_id,n_min,n_max,1,t_max)
         self.n_current=n_current


    def transform(self) -> FMSans:
         return celery_fm_to_fmsans(self.feature_model,self.n_min_job,self.n_current,self.n_max_job,self.current_task,self.n_tasks,self.max_time)


def celery_fm_to_fmsans(feature_model: FeatureModel, n_min: int, n_current: int, n_max: int, division_id: int,divisions_max: int,t_max: int) -> FMSans:
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
    
    valid_transformed_numbers_trees = trans_vector.get_valid_transformations_ids_celery(fm, divisions_max,division_id,n_min,n_max,n_current,t_max)

    # Get FMSans instance
    return FMSans(FM(fm.root), trans_vector, valid_transformed_numbers_trees)


