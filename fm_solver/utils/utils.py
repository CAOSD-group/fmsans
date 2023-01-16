"""
This module contains generic utils.
"""

from fm_solver.models.feature_model import FM
from fm_solver.transformations.refactorings import FMRefactoring


def apply_refactoring(fm: FM, refactoring: FMRefactoring) -> FM:
    """It applies a given refactoring to all instances in the feature model."""
    instances = refactoring.get_instances(fm)
    for _, instance in enumerate(instances, 1):
        fm = refactoring.transform(fm, instance)
    return fm


