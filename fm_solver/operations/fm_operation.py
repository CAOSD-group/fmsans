from abc import abstractmethod
from typing import Any

from flamapy.core.operations import Operation

from fm_solver.models.feature_model import FM


class FMOperation(Operation):

    @staticmethod
    @abstractmethod
    def get_name() -> str:
        """Name of the operation."""
        pass

    @abstractmethod
    def execute(self, model: FM) -> 'FMOperation':
        pass

    @abstractmethod
    def get_result(self) -> Any:
        pass

    def is_applicable(self, model: FM) -> bool:
        return len(model.get_constraints()) == 0

    @staticmethod
    @abstractmethod
    def join_results(subtrees_results: list[Any], fm: FM = None) -> Any:
        """Join the result of the operation applied several exclusive subtrees."""
        pass
