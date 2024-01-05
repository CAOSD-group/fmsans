import pickle
import multiprocessing
from typing import Any

from flamapy.core.operations import Operation
from flamapy.metamodels.fm_metamodel.models import FeatureModel

from fm_solver.models.utils import TransformationsVector
from fm_solver.models.feature_model import FM
from fm_solver.utils import fm_utils
from fm_solver.operations import (
    FMFullAnalysis, 
    FMCoreFeatures, 
    FMOperation, 
    FMConfigurationsNumber
)

from flamapy.metamodels.bdd_metamodel.transformations import FmToBDD
from flamapy.metamodels.bdd_metamodel.operations import (
    BDDProductsNumber
)

from flamapy.metamodels.pysat_metamodel.transformations import FmToPysat


class FMSans():
    """A representation of a feature model by means of the list of transformations 
    that are needed to obtain an equivalent feature model without any cross-tree constraints.

    The FMSans model can only have simple constraints (i.e., requires, excludes) that will be
    eliminated by the transformations.

    The FMSans model does not need to be completely in memory, 
    and can be reconstructed by pieces in linear time thanks to the trasnformations.
    Transformations can be applied in parallel because the model is split in several independent
    pieces separated by XOR groups.

    The subsequent elimination of all constraints consecutively is codified in a transformation
    vector:
      - Transformation vector: [CTC1(R0, R1), CTC2(E0, E1), CTC3(R1, R0),..., CTCN(R0, R1)]

    Transformations are codified in a binary vector where each position represents a constraint
    (requires or excludes): 'A REQUIRES/EXCLUDES B', 
    and the binary value represent the transformation that need to be applied to 
    eliminate that constraint.
    The elimination of a constraint involved two kinds of exclusive transformations that results
    in two exclusive subtrees of the feature model:
      - for REQUIRES constraints the two transformations are:
          a) commitment the feature B.
          b) deletion of feature A, and deletion of feature B.
      - for EXCLUDES constraints the two transformations are:
          a) deletion of feature B.
          b) deletion of feature A, and commitment of the feature B.
    
    A vector is valid is the application of all its transformation result in a feature model that
    is not NIL (None or Null). All valid vectors are stored as decimal numbers in a 
    transformations id list (in fact, it is a dictionary of hash of the subtree -> transformation ids):
      - Transformations IDS: [0, 1, 2, 245,..., 5432,..., 2^n-1]
          0 0 0 0 ... 0 = 0
          0 0 0 0 ... 1 = 1
          ...
          1 1 1 1 ... 1 = 2^n-1 
    """
    def __init__(self, 
                 fm: FM,
                 transformations_vector: TransformationsVector,
                 transformations_ids: dict[str, int],
                ) -> None:
        self.fm = fm
        self.transformations_vector = transformations_vector  
        self.transformations_ids = transformations_ids  
    
    def get_feature_model(self, n_processes: int = 1) -> FeatureModel:
        """Returns the complete feature model without cross-tree constraints."""
        if self.transformations_vector is None:
            return self.fm
        pick_tree = pickle.dumps(self.fm, protocol=pickle.HIGHEST_PROTOCOL)
        subtrees = self.get_subtrees(n_processes)
        # Join all subtrees
        result_fm = pickle.loads(pick_tree)
        result_fm = fm_utils.get_model_from_subtrees(result_fm, subtrees)
        return result_fm

    def get_analysis(self, n_processes: int = 1) -> dict[str, Any]:
        if self.transformations_vector is None:
            return FMFullAnalysis().execute(self.fm).get_result()
        n_bits = self.transformations_vector.n_bits()
        pick_tree = pickle.dumps(self.fm, protocol=pickle.HIGHEST_PROTOCOL)
        results = []
        with multiprocessing.Pool(n_processes) as pool:
            items = [(pick_tree, list(format(num, f'0{n_bits}b')), FMFullAnalysis) for num in self.transformations_ids.values()]
            results_subtrees = pool.starmap_async(self._execute_paralell, items)
            results.append(results_subtrees.get())
        result_analysis = FMFullAnalysis.join_results(results, self.fm)
        return result_analysis

    # def get_analysis_bdd(self, n_processes: int = 1) -> dict[str, Any]:
    #     if self.transformations_vector is None:
    #         bdd_model = FmToBDD(self.fm).transform()
    #         return FMFullAnalysisSAT().execute(bdd_model).get_result()
    #     n_bits = self.transformations_vector.n_bits()
    #     pick_tree = pickle.dumps(self.fm, protocol=pickle.HIGHEST_PROTOCOL)
    #     with multiprocessing.Pool(n_processes) as pool:
    #         items = [(pick_tree, list(format(num, f'0{n_bits}b')), FMFullAnalysisSAT, num) for num in self.transformations_ids.values()]
    #         results_subtrees = pool.starmap_async(self._execute_paralell_bdd, items)
    #         result_analysis = FMFullAnalysisSAT.join_results(results_subtrees.get())
    #     return result_analysis

    # def get_analysis_sat(self, n_processes: int = 1) -> dict[str, Any]:
    #     if self.transformations_vector is None:
    #         sat_model = FmToPysat(self.fm).transform()
    #         return FMFullAnalysisSAT().execute(sat_model).get_result()
    #     n_bits = self.transformations_vector.n_bits()
    #     pick_tree = pickle.dumps(self.fm, protocol=pickle.HIGHEST_PROTOCOL)
    #     with multiprocessing.Pool(n_processes) as pool:
    #         items = [(pick_tree, list(format(num, f'0{n_bits}b')), FMFullAnalysisSAT, num) for num in self.transformations_ids.values()]
    #         results_subtrees = pool.starmap_async(self._execute_paralell_sat, items)
    #         result_analysis = FMFullAnalysisSAT.join_results(results_subtrees.get())
    #     return result_analysis

        # for num in self.transformations_ids.values():
        #     binary_vector = list(format(num, f'0{n_bits}b'))
        #     tree, _ = self.transformations_vector.execute(pick_tree, binary_vector)
        #     tree = fm_utils.remove_leaf_abstract_auxiliary_features(tree)
        #     analysis_result = FMFullAnalysis().execute(tree).get_result()
        #     results.append(analysis_result)
        # # Join all results
        # return FMFullAnalysis.join_results(results)

    def get_core_features(self, n_processes: int = 1) -> dict[str, Any]:
        if self.transformations_vector is None:
            return FMCoreFeatures().execute(self.fm).get_result()
        n_bits = self.transformations_vector.n_bits()
        pick_tree = pickle.dumps(self.fm, protocol=pickle.HIGHEST_PROTOCOL)
        with multiprocessing.Pool(n_processes) as pool:
            items = [(pick_tree, list(format(num, f'0{n_bits}b')), FMCoreFeatures) for num in self.transformations_ids.values()]
            analysis_result = pool.starmap_async(self._execute_paralell, items)
            result = set.intersection(*analysis_result.get())
        return result

    def get_core_features_bdd(self, n_processes: int = 1) -> dict[str, Any]:
        if self.transformations_vector is None:
            bdd_model = FmToBDD(self.fm).transform()
            return BDDCoreFeatures().execute(bdd_model).get_result()
        n_bits = self.transformations_vector.n_bits()
        pick_tree = pickle.dumps(self.fm, protocol=pickle.HIGHEST_PROTOCOL)
        with multiprocessing.Pool(n_processes) as pool:
            items = [(pick_tree, list(format(num, f'0{n_bits}b')), BDDCoreFeatures) for num in self.transformations_ids.values()]
            analysis_result = pool.starmap_async(self._execute_paralell_bdd, items)
            result = set.intersection(*analysis_result.get())
        return result

    def get_number_of_configurations(self, n_processes: int = 1) -> dict[str, Any]:
        if self.transformations_vector is None:
            return FMConfigurationsNumber().execute(self.fm).get_result()
        n_bits = self.transformations_vector.n_bits()
        pick_tree = pickle.dumps(self.fm, protocol=pickle.HIGHEST_PROTOCOL)
        with multiprocessing.Pool(n_processes) as pool:
            items = [(pick_tree, list(format(num, f'0{n_bits}b')), FMConfigurationsNumber) for num in self.transformations_ids.values()]
            analysis_result = pool.starmap_async(self._execute_paralell, items)
            result = FMConfigurationsNumber.join_results(analysis_result.get())
        return result

    def get_number_of_configurations_bdd(self, n_processes: int = 1) -> dict[str, Any]:
        if self.transformations_vector is None:
            bdd_model = FmToBDD(self.fm).transform()
            return BDDProductsNumber().execute(bdd_model).get_result()
        n_bits = self.transformations_vector.n_bits()
        pick_tree = pickle.dumps(self.fm, protocol=pickle.HIGHEST_PROTOCOL)
        with multiprocessing.Pool(n_processes) as pool:
            items = [(pick_tree, list(format(num, f'0{n_bits}b')), BDDProductsNumber, num) for num in self.transformations_ids.values()]
            analysis_result = pool.starmap_async(self.execute_paralell_bdd, items)
            result = FMConfigurationsNumber.join_results(analysis_result.get(), self.fm)
        return result
    
    # def get_number_of_configurations_sat(self, n_processes: int = 1) -> dict[str, Any]:
    #     if self.transformations_vector is None:
    #         sat_model = FmToPysat(self.fm).transform()
    #         return SATProductsNumber().execute(sat_model).get_result()
    #     n_bits = self.transformations_vector.n_bits()
    #     pick_tree = pickle.dumps(self.fm, protocol=pickle.HIGHEST_PROTOCOL)
    #     with multiprocessing.Pool(n_processes) as pool:
    #         items = [(pick_tree, list(format(num, f'0{n_bits}b')), SATProductsNumber, num) for num in self.transformations_ids.values()]
    #         analysis_result = pool.starmap_async(self.execute_paralell_sat, items)
    #         result = FMConfigurationsNumber.join_results(analysis_result.get(), self.fm)
    #     return result

    def execute_paralell(self, fm: bytes, binary_vector: list[str], op: FMOperation) -> Any:
        tree, _ = self.transformations_vector.execute(fm, binary_vector)
        tree = fm_utils.remove_leaf_abstract_auxiliary_features(tree)
        return op().execute(tree).get_result()

    def _execute_paralell(self, fm: bytes, binary_vector: list[str], op: FMOperation) -> Any:
        tree, _ = self.transformations_vector.execute(fm, binary_vector)
        tree = fm_utils.remove_leaf_abstract_auxiliary_features(tree)
        return op().execute(tree).get_result()

    def execute_paralell_bdd(self, fm: bytes, binary_vector: list[str], op: FMOperation, num: int) -> Any:
        tree, _ = self.transformations_vector.execute(fm, binary_vector)
        tree = fm_utils.remove_leaf_abstract_auxiliary_features(tree)
        bdd_model = FmToBDD(tree, f'{tree.root.name}{num}').transform()
        return op().execute(bdd_model).get_result()

    # def execute_paralell_sat(self, fm: bytes, binary_vector: list[str], op: FMOperation, num: int) -> Any:
    #     tree, _ = self.transformations_vector.execute(fm, binary_vector)
    #     tree = fm_utils.remove_leaf_abstract_auxiliary_features(tree)
    #     sat_model = FmToPysat(tree).transform()
    #     return op().execute(sat_model).get_result()

    def _subtrees_execute_paralell(self, fm: bytes, binary_vector: list[str]) -> FM:
        tree, _ = self.transformations_vector.execute(fm, binary_vector)
        tree = fm_utils.remove_leaf_abstract_auxiliary_features(tree)
        return tree

    def get_subtrees(self, n_processes: int = 1) -> list[FM]:
        if self.transformations_vector is None:
            return [self.fm]
        n_bits = self.transformations_vector.n_bits()
        pick_tree = pickle.dumps(self.fm, protocol=pickle.HIGHEST_PROTOCOL)
        with multiprocessing.Pool(n_processes) as pool:
            items = [(pick_tree, list(format(num, f'0{n_bits}b'))) for num in self.transformations_ids.values()]
            results_subtrees = pool.starmap_async(self._subtrees_execute_paralell, items)
            subtrees = results_subtrees.get()
        return subtrees


# def fmsans_stats(fm: FMSans) -> str:
#     features_without_implications = 0 if fm.subtree_without_constraints_implications is None else len(fm.subtree_without_constraints_implications.get_features())
#     features_with_implications = 0 if fm.subtree_with_constraints_implications is None else len(fm.subtree_with_constraints_implications.get_features())
#     unique_features = set() if fm.subtree_without_constraints_implications is None else {f for f in fm.subtree_without_constraints_implications.get_features()}
#     unique_features = unique_features if fm.subtree_with_constraints_implications is None else unique_features.union({f for f in fm.subtree_with_constraints_implications.get_features()})
#     constraints = 0 if fm.transformations_vector is None else len(fm.transformations_vector)
#     requires_ctcs = 0 if fm.transformations_vector is None else len([ctc for ctc in fm.transformations_vector if ctc[0].type == SimpleCTCTransformation.REQUIRES])
#     excludes_ctcs = 0 if fm.transformations_vector is None else len([ctc for ctc in fm.transformations_vector if ctc[0].type == SimpleCTCTransformation.EXCLUDES])
#     subtrees = 0 if fm.transformations_ids is None else len(fm.transformations_ids)
#     lines = []
#     lines.append(f'FMSans stats:')
#     lines.append(f'  #Features:            {features_without_implications + features_with_implications}')
#     lines.append(f'    #Unique Features:   {len(unique_features)}')
#     lines.append(f'    #Features out CTCs: {features_without_implications}')
#     lines.append(f'    #Features in CTCs:  {features_with_implications}')
#     lines.append(f'  #Constraints:         {constraints}')
#     lines.append(f'    #Requires:          {requires_ctcs}')
#     lines.append(f'    #Excludes:          {excludes_ctcs}')
#     lines.append(f'  #Subtrees:            {subtrees}')
#     return '\n'.join(lines)


# def fm2fmsans(fm: FM, n_cores: int = 1) -> FMSans:
#     assert not any(constraints_utils.is_complex_constraint(ctc) for ctc in fm.get_constraints())
    
#     if fm.get_constraints():  # The feature model has constraints.
#         # Split the feature model into two
#         subtree_with_constraints_implications, subtree_without_constraints_implications = fm_utils.get_subtrees_constraints_implications(fm)
#         #subtree_with_constraints_implications, subtree_without_constraints_implications = fm, None
        
#         # Get constraints order
#         constraints_order = get_basic_constraints_order(fm)

#         # Get transformations vector
#         transformations_vector = get_transformations_vector(constraints_order)

#         # Get valid transformations ids.
#         ### PARALLEL CODE
#         valid_transformed_numbers_trees = {}
#         queue = Queue()
#         processes = []
#         n_bits = len(constraints_order[0])
#         cpu_count = n_cores
#         n_processes = cpu_count if n_bits > cpu_count else 1
#         pick_tree = pickle.dumps(subtree_with_constraints_implications, protocol=pickle.HIGHEST_PROTOCOL)
#         for process_i in range(n_processes):
#             min_id, max_id = get_min_max_ids_transformations_for_parallelization(n_bits, n_processes, process_i)
#             p = Process(target=get_valid_transformations_ids, args=(pick_tree, transformations_vector, min_id, max_id, queue))
#             p.start()
#             processes.append(p)

#         for p in processes:
#             valid_ids = queue.get()
#             valid_transformed_numbers_trees.update(valid_ids)
#         ### End of parallel code.

#         # Get FMSans instance
#         fm_sans_model = FMSans(subtree_with_constraints_implications=subtree_with_constraints_implications, 
#                         subtree_without_constraints_implications=subtree_without_constraints_implications,
#                         transformations_vector=transformations_vector,
#                         transformations_ids=valid_transformed_numbers_trees)
#     else:  # The feature model has not any constraint.
#         fm_sans_model = FMSans(None, fm, [], {})
#     return fm_sans_model