"""
This module contains generic utils.
"""

import os

from fm_solver.models.feature_model import FM
from fm_solver.transformations.refactorings import FMRefactoring


def apply_refactoring(fm: FM, refactoring: FMRefactoring) -> FM:
    """It applies a given refactoring to all instances in the feature model."""
    instances = refactoring.get_instances(fm)
    for i, instance in enumerate(instances, 1):
        print(f'{refactoring.get_name()}: {i}/{len(instances)} ({i/len(instances)*100}%). CTC: {instance}')
        fm = refactoring.transform(fm, instance)
    return fm


def int_to_scientific_notation(n: int, precision: int = 2) -> str:
    """Convert a large int into scientific notation.
    
    It is required for large numbers that Python cannot convert to float,
    solving the error `OverflowError: int too large to convert to float`.
    """
    if not isinstance(n, int):
        value = int(n)
    else:
        value = n
    str_n = str(value)
    decimal = str_n[1:precision+1]
    exponent = str(len(str_n) - 1)
    return str_n[0] + '.' + decimal + 'e' + exponent


def get_filespaths(dirpath: str) -> list[str]:
    """Get all file paths from the given directory path."""
    models = []
    for root, dirs, files in os.walk(dirpath):
        for file in files:
            filepath = os.path.join(root, file)
            models.append(filepath)
    return models


def get_filename_from_filepath(filepath: str) -> str:
    return '.'.join(os.path.basename(filepath).split('.')[:-1])