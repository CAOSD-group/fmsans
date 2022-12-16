"""
This module contains generic utils.
"""

from flamapy.metamodels.fm_metamodel.models import FeatureModel

from fm_solver.transformations.refactorings import FMRefactoring
from fm_solver.utils import logging_utils


def apply_refactoring(fm: FeatureModel, refactoring: FMRefactoring) -> FeatureModel:
    """It applies a given refactoring to all instances in the feature model."""
    instances = refactoring.get_instances(fm)
    logging_utils.LOGGER.debug(f'Applying {refactoring.get_name()} to {len(instances)} instances.')
    for _, instance in enumerate(instances, 1):
        logging_utils.LOGGER.debug(f'Applying {refactoring.get_name()} to {instance}.')
        fm = refactoring.transform(fm, instance)
    return fm


