import pickle
import multiprocessing
from typing import Any

from flamapy.core.operations import Operation
from flamapy.metamodels.bdd_metamodel.transformations import FmToBDD

from fm_solver.models import FMSans
from fm_solver.models.feature_model import FM
from fm_solver.operations import FMOperation, FMFullAnalysisBDD, FMConfigurationsNumber, FMCoreFeatures, FMDeadFeatures
from fm_solver.utils import fm_utils


class FMSansFullAnalysisBDD(FMOperation):
    """It performs several analysis operations over the feature model using BDD solver."""

    @staticmethod
    def get_name() -> str:
        return 'Full analysis BDD'

    def __init__(self, n_processes: int = 1) -> None:
        self._result = {}
        self.fmsans = None
        self.n_processes = n_processes

    def execute(self, model: FMSans) -> 'FMSansFullAnalysisBDD':
        self.fmsans = model
        self._result = self.get_full_analysis()
        return self

    def get_result(self) -> dict[str, Any]:
        return self._result

    def get_full_analysis(self) -> dict[str, Any]:
        return full_analysis(self.fmsans, self.n_processes)
    
    @staticmethod
    def join_results(subtrees_results: list[int], fm: FM) -> dict[str, Any]:
        if not subtrees_results:
            return {FMConfigurationsNumber.get_name(): 0, 
                    FMCoreFeatures.get_name(): set()}
                    #FMDeadFeatures.get_name(): set()}
        result = {}
        result[FMConfigurationsNumber.get_name()] = FMConfigurationsNumber.join_results([r[FMConfigurationsNumber.get_name()] for r in subtrees_results])
        result[FMCoreFeatures.get_name()] = FMCoreFeatures.join_results([r[FMCoreFeatures.get_name()] for r in subtrees_results])
        #result[FMDeadFeatures.get_name()] = FMDeadFeatures.join_results([r[FMDeadFeatures.get_name()] for r in subtrees_results], fm)
        return result


def full_analysis(fmsans: FMSans, n_processes: int = 1) -> dict[str, Any]:
    if fmsans.transformations_vector is None:
        bdd_model = FmToBDD(fmsans.fm).transform()
        return FMFullAnalysisBDD().execute(bdd_model).get_result()
    n_bits = fmsans.transformations_vector.n_bits()
    pick_tree = pickle.dumps(fmsans.fm, protocol=pickle.HIGHEST_PROTOCOL)
    with multiprocessing.Pool(n_processes) as pool:
        items = [(fmsans, pick_tree, list(format(num, f'0{n_bits}b')), FMFullAnalysisBDD, num) for num in fmsans.transformations_ids.values()]
        analysis_result = pool.starmap_async(execute_paralell, items)
        result = FMFullAnalysisBDD.join_results(analysis_result.get(), fmsans.fm)
    return result


def execute_paralell(fmsans: FMSans, fm: bytes, binary_vector: list[str], op: Operation, num: int) -> Any:
    tree, _ = fmsans.transformations_vector.execute(fm, binary_vector)
    tree = fm_utils.remove_leaf_abstract_auxiliary_features(tree)
    bdd_model = FmToBDD(tree, f'{tree.root.name}{num}').transform()
    return op().execute(bdd_model).get_result()