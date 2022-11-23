"""
This module contains generic utils.
"""

from flamapy.core.models import ASTOperation
from flamapy.metamodels.fm_metamodel.models import FeatureModel, Constraint

from fm_solver.transformations.refactorings import FMRefactoring


def apply_refactoring(fm: FeatureModel, refactoring: FMRefactoring) -> FeatureModel:
    """It applies a given refactoring to all instances in the feature model."""
    instances = refactoring.get_instances(fm)
    for i, instance in enumerate(instances, 1):
        #print(f'   |->Instance {i}: {str(instance)}')
        fm = refactoring.transform(fm, instance)
    return fm


