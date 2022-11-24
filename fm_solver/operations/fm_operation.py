from abc import abstractmethod
from typing import Any

from flamapy.core.operations import Operation

from fm_solver.models import FMSans


class FMOperation(Operation):

    @staticmethod
    @abstractmethod
    def get_name() -> str:
        """Name of the operation."""
        pass

    @abstractmethod
    def execute(self, model: FMSans) -> 'FMOperation':
        pass

    @abstractmethod
    def get_result(self) -> Any:
        pass

    def is_applicable(self, model: FMSans) -> bool:
        return len(model.get_constraints()) == 0
