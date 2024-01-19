import pickle
import multiprocessing
from typing import Any

from flamapy.core.operations import Operation

from fm_solver.models import FMSans
from fm_solver.operations import FMOperation, FMConfigurationsNumber
from fm_solver.utils import fm_utils


class FMSansProductsNumber(FMOperation):
    """It computes the number of configurations of the feature model."""

    @staticmethod
    def get_name() -> str:
        return 'Configurations number'

    def __init__(self, n_processes: int = 1) -> None:
        self._result = 0
        self.fmsans = None
        self.n_processes = n_processes

    def execute(self, model: FMSans) -> 'FMSansProductsNumber':
        self.fmsans = model
        self._result = self.get_configurations_number()
        return self

    def get_result(self) -> int:
        return self._result

    def get_configurations_number(self) -> int:
        return configurations_number(self.fmsans, self.n_processes)
    
    @staticmethod
    def join_results(subtrees_results: list[int]) -> int:
        return sum(subtrees_results)


def configurations_number(fmsans: FMSans, n_processes: int = 1) -> int:
    if fmsans.transformations_vector is None:
        return FMConfigurationsNumber().execute(fmsans.fm).get_result()
    n_bits = fmsans.transformations_vector.n_bits()
    pick_tree = pickle.dumps(fmsans.fm, protocol=pickle.HIGHEST_PROTOCOL)
    with multiprocessing.Pool(n_processes) as pool:
        items = [(fmsans, pick_tree, list(format(num, f'0{n_bits}b')), FMConfigurationsNumber) for num in fmsans.transformations_ids.values()]
        analysis_result = pool.starmap_async(execute_paralell, items)
        result = FMSansProductsNumber.join_results(analysis_result.get())
    return result


def execute_paralell(fmsans: FMSans, fm: bytes, binary_vector: list[str], op: Operation) -> Any:
    tree, _ = fmsans.transformations_vector.execute(fm, binary_vector)
    tree = fm_utils.remove_leaf_abstract_auxiliary_features(tree)
    return op().execute(tree).get_result()