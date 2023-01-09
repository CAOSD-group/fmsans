from abc import abstractmethod
from typing import Any

from flamapy.core.operations import Operation
from flamapy.metamodels.fm_metamodel.models import FeatureModel


class FMOperation(Operation):

    @staticmethod
    @abstractmethod
    def get_name() -> str:
        """Name of the operation."""
        pass

    @abstractmethod
    def execute(self, model: FeatureModel) -> 'FMOperation':
        pass

    @abstractmethod
    def get_result(self) -> Any:
        pass

    def is_applicable(self, model: FeatureModel) -> bool:
        return len(model.get_constraints()) == 0

    @staticmethod
    @abstractmethod
    def join_results(subtrees_results: list[Any]) -> Any:
        """Join the result of the operation applied several exclusive subtrees."""
        pass
