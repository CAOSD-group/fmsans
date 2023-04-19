import pickle
import multiprocessing

from flamapy.metamodels.fm_metamodel.models import Feature

from fm_solver.models import FMSans
from fm_solver.operations import FMOperation, FMCoreFeatures


class FMSansCoreFeatures(FMOperation):

    @staticmethod
    def get_name() -> str:
        return 'Core features'

    def __init__(self, n_processes: int = 1) -> None:
        self._result = set()
        self.fmsans = None
        self.n_processes = n_processes

    def execute(self, model: FMSans) -> 'FMSansCoreFeatures':
        self.fmsans = model
        self._result = self.get_core_features()
        return self

    def get_result(self) -> set[Feature]:
        return self._result

    def get_core_features(self) -> set[Feature]:
        return core_features(self.fmsans, self.n_processes)
    
    @staticmethod
    def join_results(subtrees_results: list[set[Feature]]) -> set[Feature]:
        return set.intersection(*subtrees_results)


def core_features(fmsans: FMSans, n_processes: int = 1) -> set[Feature]:
    if fmsans.transformations_vector is None:
        return FMCoreFeatures().execute(fmsans.fm).get_result()
    n_bits = fmsans.transformations_vector.n_bits()
    pick_tree = pickle.dumps(fmsans.fm, protocol=pickle.HIGHEST_PROTOCOL)
    with multiprocessing.Pool(n_processes) as pool:
        items = [(pick_tree, list(format(num, f'0{n_bits}b')), FMCoreFeatures) for num in fmsans.transformations_ids.values()]
        analysis_result = pool.starmap_async(fmsans.execute_paralell, items)
        result = FMSansCoreFeatures.join_results(analysis_result.get())
    return result
