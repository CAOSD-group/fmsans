import pickle
import multiprocessing
from typing import Any

from fm_solver.models import FMSans
from fm_solver.operations import (
    FMOperation, 
    FMFullAnalysis,
    FMConfigurationsNumber,
    FMCoreFeatures
)


class FMSansFullAnalysis(FMOperation):

    @staticmethod
    def get_name() -> str:
        return 'Full analysis'

    def __init__(self, n_processes: int = 1) -> None:
        self._result = {}
        self.fmsans = None
        self.n_processes = n_processes

    def execute(self, model: FMSans) -> 'FMSansFullAnalysis':
        self.fmsans = model
        self._result = self.get_full_analysis()
        return self

    def get_result(self) -> dict[str, Any]:
        return self._result

    def get_full_analysis(self) -> dict[str, Any]:
        return full_analysis(self.fmsans, self.n_processes)
    
    @staticmethod
    def join_results(subtrees_results: list[int]) -> dict[str, Any]:
        if not subtrees_results:
            return {FMFullAnalysis.CONFIGURATIONS_NUMBER: 0, 
                    FMFullAnalysis.CORE_FEATURES: set()}
        result = {}
        result[FMFullAnalysis.CONFIGURATIONS_NUMBER] = FMConfigurationsNumber.join_results([r[FMFullAnalysis.CONFIGURATIONS_NUMBER] for r in subtrees_results])
        result[FMFullAnalysis.CORE_FEATURES] = FMCoreFeatures.join_results([r[FMFullAnalysis.CORE_FEATURES] for r in subtrees_results])
        return result


def full_analysis(fmsans: FMSans, n_processes: int = 1) -> dict[str, Any]:
    if fmsans.transformations_vector is None:
        return FMFullAnalysis().execute(fmsans.fm).get_result()
    n_bits = fmsans.transformations_vector.n_bits()
    pick_tree = pickle.dumps(fmsans.fm, protocol=pickle.HIGHEST_PROTOCOL)
    with multiprocessing.Pool(n_processes) as pool:
        items = [(pick_tree, list(format(num, f'0{n_bits}b')), FMFullAnalysis) for num in fmsans.transformations_ids.values()]
        analysis_result = pool.starmap_async(fmsans.execute_paralell, items)
        result = FMSansFullAnalysis.join_results(analysis_result.get())
    return result
