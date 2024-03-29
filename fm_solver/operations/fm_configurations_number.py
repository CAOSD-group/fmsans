import math

from flamapy.metamodels.fm_metamodel.models import Feature

from fm_solver.models.feature_model import FM
from fm_solver.operations import FMOperation


class FMConfigurationsNumber(FMOperation):
    """It computes the number of configurations of the feature model."""

    @staticmethod
    def get_name() -> str:
        return 'Configurations number'

    def __init__(self) -> None:
        self._result = 0
        self.feature_model = None

    def execute(self, model: FM) -> 'FMConfigurationsNumber':
        self.feature_model = model
        self._result = self.get_configurations_number()
        return self

    def get_result(self) -> int:
        return self._result

    def get_configurations_number(self) -> int:
        return configurations_number(self.feature_model)
    
    @staticmethod
    def join_results(subtrees_results: list[int]) -> int:
        return sum(subtrees_results)


def configurations_number(fm: FM) -> int:
    return configurations_number_rec(fm.root)


# def configurations_number_rec(feature: Feature) -> int:
#     if feature.is_leaf():
#         return 1
#     counts = []
#     for relation in feature.get_relations():
#         if relation.is_mandatory():
#             counts.append(configurations_number_rec(relation.children[0]))
#         elif relation.is_optional():
#             counts.append(configurations_number_rec(relation.children[0]) + 1)
#         elif relation.is_alternative():
#             counts.append(sum((configurations_number_rec(f) for f in relation.children)))
#         elif relation.is_or():
#             children_counts = [configurations_number_rec(f) + 1 for f in relation.children]
#             counts.append(math.prod(children_counts) - 1)
#     return math.prod(counts)

def configurations_number_rec(feature: Feature) -> int:
    if feature.is_leaf():
        return 1
    counts = 1
    for relation in feature.get_relations():
        if relation.is_mandatory():
            counts *= configurations_number_rec(relation.children[0])
        elif relation.is_optional():
            counts *= configurations_number_rec(relation.children[0]) + 1
        elif relation.is_alternative():
            counts *= sum((configurations_number_rec(f) for f in relation.children))
        elif relation.is_or():
            children_counts = [configurations_number_rec(f) + 1 for f in relation.children]
            counts *= math.prod(children_counts) - 1
    return counts