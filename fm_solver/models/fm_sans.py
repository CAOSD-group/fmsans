import pickle
import math
import copy
import multiprocessing
from multiprocessing import Process, Queue
from typing import Any
from collections.abc import Callable

from flamapy.metamodels.fm_metamodel.models import (
    Feature, 
    Relation, 
    Constraint, 
    Attribute
)

from fm_solver.models.feature_model import FM
from fm_solver.utils import fm_utils, constraints_utils
from fm_solver.operations import FMFullAnalysis


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
                 subtree_with_constraints_implications: FM,
                 subtree_without_constraints_implications: FM,
                 transformations_vector: list[tuple['SimpleCTCTransformation', 'SimpleCTCTransformation']],
                 transformations_ids: dict[str, int],
                ) -> None:
        self.subtree_with_constraints_implications = subtree_with_constraints_implications
        self.subtree_without_constraints_implications = subtree_without_constraints_implications
        # Order of the transformations of the constraints
        self.transformations_vector = transformations_vector  
        # Numbers of the transformations
        self.transformations_ids = transformations_ids  
    
    def get_feature_model(self) -> FM:
        """Returns the complete feature model without cross-tree constraints."""
        if self.subtree_with_constraints_implications is None:
            return self.subtree_without_constraints_implications
        subtrees = set()
        n_bits = len(self.transformations_vector)
        max = len(self.transformations_ids)
        pick_tree = pickle.dumps(self.subtree_with_constraints_implications, protocol=pickle.HIGHEST_PROTOCOL)
        for i, num in enumerate(self.transformations_ids.values()):
            binary_vector = list(format(num, f'0{n_bits}b'))
            tree, _ = execute_transformations_vector(pick_tree, self.transformations_vector, binary_vector)
            tree = fm_utils.remove_leaf_abstract_auxiliary_features(tree)
            subtrees.add(tree)
            percentage = (i / max) * 100
            #logging_utils.LOGGER.debug(f'ID: {num}. {i} / {max} ({percentage}%)')
        # Join all subtrees
        #logging_utils.LOGGER.debug(f'Getting full model from {len(subtrees)} unique subtrees...')
        result_fm = fm_utils.get_model_from_subtrees(self.subtree_with_constraints_implications, subtrees)
        # Mix result FM and subtree without implications:
        # 1. Change name to the original root
        if self.subtree_without_constraints_implications is None:
            fm = result_fm
        else:
            #logging_utils.LOGGER.debug(f'Joining subtrees to subtree without CTCs implications...')
            #self.subtree_without_constraints_implications.root.name = fm_utils.get_new_feature_name(result_fm, 'Root')  # This is not needed.
            new_root = Feature(fm_utils.get_new_feature_name(result_fm, 'Root'), is_abstract=True)  # We can use the same feature's name for Root.
            #new_root = Feature(result_fm.root.name, is_abstract=True)   # We may use the same feature's name for Root.
            aux_attribute = Attribute(name=FM.AUXILIARY_FEATURES_ATTRIBUTE, domain=None, default_value=None, null_value=None)
            aux_attribute.set_parent(new_root)
            new_root.add_attribute(aux_attribute)
            new_root.add_relation(Relation(new_root, [self.subtree_without_constraints_implications.root], 1, 1))
            self.subtree_without_constraints_implications.root.parent = new_root
            new_root.add_relation(Relation(new_root, [result_fm.root], 1, 1))
            result_fm.root.parent = new_root

            fm = FM(new_root)
        #logging_utils.LOGGER.debug(f'Removing {sum(f.is_abstract for f in fm.get_features())} abstract features...')
        #with timer.Timer(logger=logging_utils.LOGGER.info, message="Removing abstract features."): 
        #fm = fm_utils.remove_leaf_abstract_features(fm)
        return fm

    def get_analysis(self) -> dict[str, Any]:
        if self.subtree_with_constraints_implications is None:
            return FMFullAnalysis().execute(self.subtree_without_constraints_implications).get_result()
        n_bits = len(self.transformations_vector)
        max = len(self.transformations_ids)
        results: list[dict[str, Any]] = []
        total_configs = 0
        #subtrees = set()  # usar mejor un dictionary de hash -> resultado de analysis (así evitamos el "if")
        pick_tree = pickle.dumps(self.subtree_with_constraints_implications, protocol=pickle.HIGHEST_PROTOCOL)
        for i, num in enumerate(self.transformations_ids.values()):
            binary_vector = list(format(num, f'0{n_bits}b'))
            tree, _ = execute_transformations_vector(pick_tree, self.transformations_vector, binary_vector)
            tree = fm_utils.remove_leaf_abstract_auxiliary_features(tree)
            #h = hash(tree)
            #if h not in subtrees:
                #subtrees.add(h)
            analysis_result = FMFullAnalysis().execute(tree).get_result()
            total_configs += analysis_result[FMFullAnalysis.CONFIGURATIONS_NUMBER]
            
            results.append(analysis_result)
            #percentage = (i / max) * 100
            #logging_utils.LOGGER.debug(f'ID: {num}. {i} / {max} ({percentage}%)')
        # Join all subtrees
        result = FMFullAnalysis.join_results(results)
        #logging_utils.LOGGER.debug(f'Joining results from {max} unique subtrees...')
        # Join result with subtree without CTCs implications
        if self.subtree_without_constraints_implications is not None:
            result_subtree_without_constraints = FMFullAnalysis().execute(self.subtree_without_constraints_implications).get_result()
            analysis_result = {}
            analysis_result[FMFullAnalysis.CONFIGURATIONS_NUMBER] = result[FMFullAnalysis.CONFIGURATIONS_NUMBER] * result_subtree_without_constraints[FMFullAnalysis.CONFIGURATIONS_NUMBER]
            analysis_result[FMFullAnalysis.CORE_FEATURES] = result[FMFullAnalysis.CORE_FEATURES].union(result_subtree_without_constraints[FMFullAnalysis.CORE_FEATURES])
            result = analysis_result
        return result
        

class SimpleCTCTransformation():
    """It represents a transformation of a simple cross-tree constraint (requires or excludes),
    codified in binary.

    It contains:
        - a name being 'R' for requires constraints, and 'E' for excludes constraints.
        - a value being 0 for the first transformation and 1 for the second transformation.
        - a list of functions that implement the transformation.
        - a list of features (the features of the constraint) to which the transformation will be applied.
    """
    REQUIRES = 'R'
    EXCLUDES = 'E'
    REQUIRES_T0 = [fm_utils.commitment_feature]
    REQUIRES_T1 = [fm_utils.deletion_feature, fm_utils.deletion_feature]
    EXCLUDES_T0 = [fm_utils.deletion_feature]
    EXCLUDES_T1 = [fm_utils.deletion_feature, fm_utils.commitment_feature]

    def __init__(self, type: str, value: int, transformations: list[Callable], features: list[str]) -> None:
        self.type = type
        self.value = value  # the value is not needed at all?
        self.transformations = transformations
        self.features = features

    def transforms(self, fm: FM, copy_model: bool = False, features_already_executed: tuple[set[str], set[str]] = None) -> FM:
        return fm_utils.transform_tree(self.transformations, fm, self.features, copy_model, features_already_executed)

    def __hash__(self) -> int:
        return hash((
            self.type,
            self.value,
            self.transformations,
            self.features
        ))

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, SimpleCTCTransformation) and
            self.type == other.type and
            self.value == other.value and
            self.transformations == other.transformations and
            self.features == other.features
        )

    def __str__(self) -> str:
        return f'{self.type}{self.value}{[f for f in self.features]}'


def get_transformations_vector(constraints_order: tuple[list[Constraint], dict[int, tuple[int, int]]]) -> list[tuple[SimpleCTCTransformation, SimpleCTCTransformation]]:
    """Get the transformations vector from a specific constraints order.
    
    Keyword arguments:
    constraints_order -- A tuple with the list of constraints in order, and a dictionary with the 
                         index of the constraints and a tuple of (0,1) or (1,0) indicating the 
                         transformation that corresponds with the first transformation or the 
                         second transformation. 0 is the first transformation; 1 is the second one.
    """
    transformations_vector = []
    for i, ctc in enumerate(constraints_order[0], 0):
        #print(f'i: {i}, ctc: {ctc}')
        left_feature, right_feature = constraints_utils.left_right_features_from_simple_constraint(ctc)
        if constraints_utils.is_requires_constraint(ctc):
            t0 = SimpleCTCTransformation(SimpleCTCTransformation.REQUIRES, 0, SimpleCTCTransformation.REQUIRES_T0, [right_feature])
            t1 = SimpleCTCTransformation(SimpleCTCTransformation.REQUIRES, 1, SimpleCTCTransformation.REQUIRES_T1, [left_feature, right_feature])
        else:  # it is an excludes
            t0 = SimpleCTCTransformation(SimpleCTCTransformation.EXCLUDES, 0, SimpleCTCTransformation.EXCLUDES_T0, [right_feature])
            t1 = SimpleCTCTransformation(SimpleCTCTransformation.EXCLUDES, 1, SimpleCTCTransformation.EXCLUDES_T1, [left_feature, right_feature])
        if constraints_order[1][i] == (0, 1):
            transformations_vector.append((t0, t1))
        else:
            # t0.value = 1  # the value is not needed at all?
            # t1.value = 0  # the value is not needed at all?
            transformations_vector.append((t1, t0))
    return transformations_vector


def execute_transformations_vector(fm: bytes, 
                                   transformations_vector: list[tuple[SimpleCTCTransformation, SimpleCTCTransformation]], 
                                   binary_vector: list[str]) -> tuple[FM, int]:
    """Execute a transformations vector according to the binary number of the vector provided.
    
    It returns the resulting model and the transformation (bit) that fails in case of a
    transformation returns NIL (None).
    """
    #assert len(transformations_vector) == len(binary_vector)

    #tree = FeatureModel(copy.deepcopy(fm.root))
    tree = pickle.loads(fm)
    i = 0
    commitment_features = set()  # Set of features already commitment in this tree.
    deletion_features = set()  # Set of features already deleted in this tree.
    while i < len(transformations_vector) and tree is not None:
        tree = transformations_vector[i][int(binary_vector[i])].transforms(tree, False, (commitment_features, deletion_features))
        i += 1
    return (tree, i-1)





def fmsans_stats(fm: FMSans) -> str:
    features_without_implications = 0 if fm.subtree_without_constraints_implications is None else len(fm.subtree_without_constraints_implications.get_features())
    features_with_implications = 0 if fm.subtree_with_constraints_implications is None else len(fm.subtree_with_constraints_implications.get_features())
    unique_features = set() if fm.subtree_without_constraints_implications is None else {f for f in fm.subtree_without_constraints_implications.get_features()}
    unique_features = unique_features if fm.subtree_with_constraints_implications is None else unique_features.union({f for f in fm.subtree_with_constraints_implications.get_features()})
    constraints = 0 if fm.transformations_vector is None else len(fm.transformations_vector)
    requires_ctcs = 0 if fm.transformations_vector is None else len([ctc for ctc in fm.transformations_vector if ctc[0].type == SimpleCTCTransformation.REQUIRES])
    excludes_ctcs = 0 if fm.transformations_vector is None else len([ctc for ctc in fm.transformations_vector if ctc[0].type == SimpleCTCTransformation.EXCLUDES])
    subtrees = 0 if fm.transformations_ids is None else len(fm.transformations_ids)
    lines = []
    lines.append(f'FMSans stats:')
    lines.append(f'  #Features:            {features_without_implications + features_with_implications}')
    lines.append(f'    #Unique Features:   {len(unique_features)}')
    lines.append(f'    #Features out CTCs: {features_without_implications}')
    lines.append(f'    #Features in CTCs:  {features_with_implications}')
    lines.append(f'  #Constraints:         {constraints}')
    lines.append(f'    #Requires:          {requires_ctcs}')
    lines.append(f'    #Excludes:          {excludes_ctcs}')
    lines.append(f'  #Subtrees:            {subtrees}')
    return '\n'.join(lines)


def fm2fmsans(fm: FM, n_cores: int = 1) -> FMSans:
    assert not any(constraints_utils.is_complex_constraint(ctc) for ctc in fm.get_constraints())
    
    if fm.get_constraints():  # The feature model has constraints.
        # Split the feature model into two
        subtree_with_constraints_implications, subtree_without_constraints_implications = fm_utils.get_subtrees_constraints_implications(fm)
        #subtree_with_constraints_implications, subtree_without_constraints_implications = fm, None
        
        # Get constraints order
        constraints_order = get_basic_constraints_order(fm)

        # Get transformations vector
        transformations_vector = get_transformations_vector(constraints_order)

        # Get valid transformations ids.
        ### PARALLEL CODE
        valid_transformed_numbers_trees = {}
        queue = Queue()
        processes = []
        n_bits = len(constraints_order[0])
        cpu_count = n_cores
        n_processes = cpu_count if n_bits > cpu_count else 1
        pick_tree = pickle.dumps(subtree_with_constraints_implications, protocol=pickle.HIGHEST_PROTOCOL)
        for process_i in range(n_processes):
            min_id, max_id = get_min_max_ids_transformations_for_parallelization(n_bits, n_processes, process_i)
            p = Process(target=get_valid_transformations_ids, args=(pick_tree, transformations_vector, min_id, max_id, queue))
            p.start()
            processes.append(p)

        for p in processes:
            valid_ids = queue.get()
            valid_transformed_numbers_trees.update(valid_ids)
        ### End of parallel code.

        # Get FMSans instance
        fm_sans_model = FMSans(subtree_with_constraints_implications=subtree_with_constraints_implications, 
                        subtree_without_constraints_implications=subtree_without_constraints_implications,
                        transformations_vector=transformations_vector,
                        transformations_ids=valid_transformed_numbers_trees)
    else:  # The feature model has not any constraint.
        fm_sans_model = FMSans(None, fm, [], {})
    return fm_sans_model