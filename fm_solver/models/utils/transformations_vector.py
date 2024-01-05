
import os
import pickle
import math
import copy
import multiprocessing
from typing import Any
from collections.abc import Callable

from flamapy.metamodels.fm_metamodel.models import Constraint

from fm_solver.models.feature_model import FM
from fm_solver.utils import fm_utils, constraints_utils, timer


HEURISTIC_STATS_FOLDER = os.path.join('results', 'heuristics')
TIME_HEURISTIC = 'TIME_HEURISTIC'


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

    def __init__(self, type: str, value: int, functions: list[Callable], features: list[str]) -> None:
        self.type = type
        self.value = value
        self.functions = functions
        self.features = features

    def execute(self, fm: FM, copy_model: bool = False) -> FM:
        """Apply a list of functions (commitment_feature or deletion_feature) to the feature model. 
    
            For each function, it uses each feature (in order) in the features list.
        """
        tree = FM(copy.deepcopy(fm.root), fm.get_constraints()) if copy_model else fm
        for func, feature in zip(self.functions, self.features):
            if tree is not None:
                tree = func(tree, feature)
        return tree

    def __hash__(self) -> int:
        return hash((self.type, self.value, self.functions, self.features))

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, SimpleCTCTransformation) and
            self.type == other.type and
            self.value == other.value and
            self.functions == other.functions and
            self.features == other.features
        )

    def __str__(self) -> str:
        return f'{self.type}{self.value}{[f for f in self.features]}'


class TransformationsVector():
    
    def __init__(self, transformations: list[tuple[SimpleCTCTransformation, SimpleCTCTransformation]]) -> None:
        self.transformations = transformations

    @classmethod
    def from_constraints(cls, constraints: list[Constraint]) -> 'TransformationsVector':
        return TransformationsVector(cls._built_vector(constraints))

    @classmethod
    def _built_vector(cls, constraints: list[Constraint]) -> list[tuple[SimpleCTCTransformation, SimpleCTCTransformation]]:
        vector = []
        for ctc in constraints:
            left_feature, right_feature = constraints_utils.left_right_features_from_simple_constraint(ctc)
            if constraints_utils.is_requires_constraint(ctc):
                t0 = SimpleCTCTransformation(SimpleCTCTransformation.REQUIRES, 0, SimpleCTCTransformation.REQUIRES_T0, [right_feature])
                t1 = SimpleCTCTransformation(SimpleCTCTransformation.REQUIRES, 1, SimpleCTCTransformation.REQUIRES_T1, [left_feature, right_feature])
            else:  # it is an excludes
                t0 = SimpleCTCTransformation(SimpleCTCTransformation.EXCLUDES, 0, SimpleCTCTransformation.EXCLUDES_T0, [right_feature])
                t1 = SimpleCTCTransformation(SimpleCTCTransformation.EXCLUDES, 1, SimpleCTCTransformation.EXCLUDES_T1, [left_feature, right_feature])
            vector.append((t0, t1))
        return vector

    def n_bits(self) -> int:
        return len(self.transformations)

    def execute(self, fm: bytes, binary_vector: list[str], initial_bit: int = 0, final_bit: int = None) -> tuple[FM, int]:
        """Execute a transformations vector according to the binary number of the vector provided.
        
        It returns the resulting model and the transformation (bit) that fails in case of a
        transformation returns NIL (None).

        It executes the vector from the indicate initial bit (default 0) to the final bit
        (excluded, default is the length of the transformations).
        """
        if final_bit is None:
            final_bit = self.n_bits()
        i = initial_bit
        tree = pickle.loads(fm)
        while i < final_bit and tree is not None:
            function_to_execute = int(binary_vector[i])  # T0 or T1
            transformation = self.transformations[i][function_to_execute]
            tree = transformation.execute(tree, False)
            i += 1
        return (tree, i-1)

    @staticmethod
    def get_next_number_prunning_binary_vector(binary_vector: list[str], bit: int) -> int:
        """Given a binary vector and the bit that returns NIL (None or Null),
        it returns the next decimal number to be considered (i.e., the next binary vector)."""
        stop = False
        while bit >= 0 and not stop:
            if binary_vector[bit] == '0':
                binary_vector[bit] = '1'
                stop = True
            else:
                bit -= 1
        binary_vector[bit+1:] = ['0' for _ in binary_vector[bit+1:]] 
        num = int(''.join(binary_vector), 2)
        if bit < 0:
            num = 2**len(binary_vector)
        return num

    def _get_valid_transformations_ids(self, 
                                       fm: FM, 
                                       initial_bit: int = 0,  # Initial bit to be executed
                                       min_id: int = None,
                                       max_id: int = None,  # included
                                       queue: multiprocessing.Queue = None) -> dict[str, int]:
        """Return all valid transformations ids for this transformations vector in the given model.
        
        It executes the vector from the min_id number to the max_id number (included).
        For efficiency, it pre-calculated the intermediate model from 0 to the initial_bit 
        (default 0).
        """
        with timer.Timer(name=TIME_HEURISTIC, logger=None):
            n_bits = self.n_bits()
            num = 0 if min_id is None else min_id
            max_number = 2**n_bits - 1 if max_id is None else max_id
            valid_transformed_numbers_trees = {}
            #print(f'N bits: {n_bits}, initial_bit: {initial_bit}, min_id: {min_id}, max_id: {max_id}, num: {num}, max: {max_number}')
            # Pre-calculated intermediate tree for efficiency (execute the initial number until reach the initial bit)
            binary_vector = list(format(num, f'0{n_bits}b'))
            pick_tree = pickle.dumps(fm, protocol=pickle.HIGHEST_PROTOCOL)
            tree, _ = self.execute(pick_tree, binary_vector, initial_bit=0, final_bit=initial_bit)
            if tree is None:
                if queue is not None:
                    queue.put(valid_transformed_numbers_trees)
                return valid_transformed_numbers_trees
            pick_tree = pickle.dumps(tree, protocol=pickle.HIGHEST_PROTOCOL)
            # Logs variables
            _valids = 0
            _invalids_analyzed = 0
            _avoids = 0
            # Calculate valid ids
            while num <= max_number:  # Be careful! max should be included or excluded?
                binary_vector = list(format(num, f'0{n_bits}b'))
                tree, null_bit = self.execute(pick_tree, binary_vector, initial_bit=initial_bit)
                if tree is not None:
                    valid_transformed_numbers_trees[hash(tree)] = num
                    #print(f'ID (valid): {num} / {max_number} ({num/max_number}%), #Valids: {len(valid_transformed_numbers_trees)}')
                    num += 1
                    _valids += 1
                else:  # tree is None
                    jump = num
                    num = TransformationsVector.get_next_number_prunning_binary_vector(binary_vector, null_bit)
                    #print(f'ID (not valid): {num} / {max_number} ({num/max_number}%), null_bit: {null_bit}, #Valids: {len(valid_transformed_numbers_trees)}')
                    _avoids += (num - jump)
                    _invalids_analyzed += 1
            if queue is not None:
                queue.put(valid_transformed_numbers_trees)
        
        exec_time = timer.Timer.timers[TIME_HEURISTIC]
        exec_time = round(exec_time, 4)
        # print(f'#Total trees: {max_number + 1}')
        # print(f'#Valid analyzed trees: {_valids} ({_valids/max_number * 100} %)')
        # print(f'#Invalid analyzed trees: {_invalids_analyzed} ({_invalids_analyzed/max_number * 100} %)')
        # print(f'#Analyzed trees: {_valids + _invalids_analyzed} ({(_valids + _invalids_analyzed)/max_number * 100} %)')
        # print(f'#Avoid trees: {_avoids - _invalids_analyzed} ({(_avoids - _invalids_analyzed)/max_number * 100} %)')

         # Save stats in file
        outputfile_stats = os.path.join(HEURISTIC_STATS_FOLDER, f'process_{os.getpid()}.csv')
        if not os.path.exists(outputfile_stats):
            with open(outputfile_stats, 'w', encoding='utf8') as file:
                file.write(f'TotalTrees, ValidAnalyzed, InvalidAnalyzed, Analyzed, Avoid, Time(s){os.linesep}')
        with open(outputfile_stats, 'a', encoding='utf8') as file:
            file.write(f'{max_number + 1}, {_valids}, {_invalids_analyzed}, {_valids + _invalids_analyzed}, {_avoids - _invalids_analyzed}, {exec_time}{os.linesep}')
        
        return valid_transformed_numbers_trees

    def get_valid_transformations_ids(self, fm: FM, n_processes: int = 1, n_tasks: int = 1, current_task: int = 1) -> dict[str, int]:
        """Return a dict of hashes and valid transformations ids using n_processes in parallel."""
        valid_transformed_numbers_trees = {}
        queue = multiprocessing.Queue()
        processes = []
        n_bits = self.n_bits()
        #n_fixed_bits = int(math.log(n_tasks, 2)) + int(math.log(n_processes, 2))
        for process_i in range(n_processes):
            min_id, max_id, left_bits = get_min_max_ids_transformations_for_parallelization(n_bits, n_processes, process_i, n_tasks, current_task)
            p = multiprocessing.Process(target=self._get_valid_transformations_ids, args=(fm, left_bits, min_id, max_id, queue))
            p.start()
            processes.append(p)
        for p in processes:
            valid_ids = queue.get()
            valid_transformed_numbers_trees.update(valid_ids)
        return valid_transformed_numbers_trees


def get_min_max_ids_transformations_for_parallelization(n_bits: int, 
                                                        n_processes: int, 
                                                        current_process: int,
                                                        n_tasks: int = 1, 
                                                        current_task: int = 1) -> tuple[int, int, int]:
    if current_process >= n_processes:
        raise Exception(f'The current process must be in range [0, n_processes).')
    if current_task >= n_tasks:
        raise Exception(f'The current task must be in range [0, n_tasks).')
    
    left_bits_tasks = math.log(n_tasks, 2)
    left_bits_processes = math.log(n_processes, 2)
    left_bits = left_bits_tasks + left_bits_processes  # number of bits on the left
    if not left_bits.is_integer():
        raise Exception(f'The number of tasks and processes must be power of 2.')
    left_bits = int(left_bits)
    left_bits_tasks = int(left_bits_tasks)
    left_bits_processes = int(left_bits_processes)
    right_bits = n_bits - left_bits  # number of bits on the right
    binary_min_number = format(current_task, f'0{left_bits_tasks}b') + format(current_process, f'0{left_bits_processes}b') + format(0, f'0{right_bits}b')
    min_number = int(binary_min_number, 2)
    max_number = min_number + 2**right_bits - 1
    return (min_number, max_number, left_bits)
