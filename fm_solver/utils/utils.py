"""
This module contains generic utils.
"""

import logging

from flamapy.metamodels.fm_metamodel.models import FeatureModel

from fm_solver.transformations.refactorings import FMRefactoring


LOGGER = logging.getLogger('main_logger')


def apply_refactoring(fm: FeatureModel, refactoring: FMRefactoring) -> FeatureModel:
    """It applies a given refactoring to all instances in the feature model."""
    instances = refactoring.get_instances(fm)

    for i, instance in enumerate(instances, 1):
        #print(f'   |->Instance {i}: {str(instance)}')
        fm = refactoring.transform(fm, instance)
    return fm


