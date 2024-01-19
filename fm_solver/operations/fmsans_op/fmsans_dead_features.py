import pickle
import multiprocessing

from flamapy.metamodels.fm_metamodel.models import Feature

from fm_solver.models import FMSans
from fm_solver.operations import FMOperation
from fm_solver.utils import fm_utils


class FMSansDeadFeatures(FMOperation):

    @staticmethod
    def get_name() -> str:
        return 'Dead features'

    def __init__(self, n_processes: int = 1) -> None:
        self._result = set()
        self.fmsans = None
        self.n_processes = n_processes

    def execute(self, model: FMSans) -> 'FMSansDeadFeatures':
        self.fmsans = model
        self._result = self.get_dead_features()
        return self

    def get_result(self) -> set[Feature]:
        return self._result

    def get_dead_features(self) -> set[Feature]:
        return dead_features(self.fmsans, self.n_processes)
    
    @staticmethod
    def join_results(subtrees_results: list[set[Feature]]) -> set[Feature]:
        return set.union(*subtrees_results)


def dead_features(fmsans: FMSans, n_processes: int = 1) -> set[Feature]:
    if fmsans.transformations_vector is None:
        return set()
    n_bits = fmsans.transformations_vector.n_bits()
    pick_tree = pickle.dumps(fmsans.fm, protocol=pickle.HIGHEST_PROTOCOL)
    with multiprocessing.Pool(n_processes) as pool:
        items = [(fmsans, pick_tree, list(format(num, f'0{n_bits}b'))) for num in fmsans.transformations_ids.values()]
        analysis_result = pool.starmap_async(execute_paralell, items)
        result = FMSansDeadFeatures.join_results(analysis_result.get())
    
    fm = pickle.loads(pick_tree)
    fm = fm_utils.remove_leaf_abstract_auxiliary_features(fm)
    return set(fm.get_features()).difference(result)


def execute_paralell(fmsans: FMSans, fm: bytes, binary_vector: list[str]) -> set[Feature]:
    tree, _ = fmsans.transformations_vector.execute(fm, binary_vector)
    tree = fm_utils.remove_leaf_abstract_auxiliary_features(tree)
    return set(tree.get_features())