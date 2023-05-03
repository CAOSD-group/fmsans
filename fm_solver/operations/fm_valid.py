from fm_solver.models.feature_model import FM
from fm_solver.operations import FMOperation


class FMValid(FMOperation):
    """A GFT is valid if it is not empty."""

    @staticmethod
    def get_name() -> str:
        return 'Valid'

    def __init__(self) -> None:
        self.result: bool = None
        self.feature_model = None

    def get_result(self) -> bool:
        return self.result

    def execute(self, model: FM) -> 'FMValid':
        self.feature_model = model
        self.result = is_valid(model)
        return self

    def is_valid(self) -> bool:
        return is_valid(self.feature_model)

    @staticmethod
    def join_results(subtrees_results: list[set[str]]) -> bool:
        pass


def is_valid(feature_model: FM) -> bool:
    return feature_model.root is not None
