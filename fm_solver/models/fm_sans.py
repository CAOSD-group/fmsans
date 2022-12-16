import copy
from collections.abc import Callable

from flamapy.metamodels.fm_metamodel.models import FeatureModel, Feature, Relation, Constraint

from fm_solver.utils import fm_utils, constraints_utils


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
    transformations id list:
      - Transformations IDS: [0, 1, 2, 245,..., 5432,..., 2^n-1]
          0 0 0 0 ... 0 = 0
          0 0 0 0 ... 1 = 1
          ...
          1 1 1 1 ... 1 = 2^n-1 
    """

    def __init__(self, 
                 subtree_with_constraints_implications: FeatureModel,
                 subtree_without_constraints_implications: FeatureModel,
                 transformations_vector: list[tuple['SimpleCTCTransformation', 'SimpleCTCTransformation']],
                 transformations_ids: list[int],
                ) -> None:
        self.subtree_with_constraints_implications = subtree_with_constraints_implications
        self.subtree_without_constraints_implications = subtree_without_constraints_implications
        # Order of the transformations of the constraints
        self.transformations_vector = transformations_vector  
        # Numbers of the transformations
        self.transformations_ids = transformations_ids  
    
    def get_feature_model(self) -> FeatureModel:
        """Returns the complete feature model without cross-tree constraints."""
        if self.subtree_with_constraints_implications is None:
            return self.subtree_without_constraints_implications
        subtrees = set()
        n_bits = len(self.transformations_vector)
        for num in self.transformations_ids:
            binary_vector = list(format(num, f'0{n_bits}b'))
            tree, _ = execute_transformations_vector(self.subtree_with_constraints_implications, self.transformations_vector, binary_vector)
            subtrees.add(tree)
        # Join all subtrees
        result_fm = fm_utils.get_model_from_subtrees(self.subtree_with_constraints_implications, subtrees)
        # Mix result FM and subtree without implications:
        # 1. Change name to the original root
        if self.subtree_without_constraints_implications is None:
            fm = result_fm
        else:
            self.subtree_without_constraints_implications.root.name = fm_utils.get_new_feature_name(result_fm, 'Root')
            new_root = Feature(fm_utils.get_new_feature_name(result_fm, 'Root'), is_abstract=True)
            new_root.add_relation(Relation(new_root, [self.subtree_without_constraints_implications.root], 1, 1))
            self.subtree_without_constraints_implications.root.parent = new_root
            new_root.add_relation(Relation(new_root, [result_fm.root], 1, 1))
            result_fm.root.parent = new_root

            fm = FeatureModel(new_root)
        fm = fm_utils.remove_leaf_abstract_features(fm)
        return fm


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

    def transforms(self, fm: FeatureModel, copy_model: bool = False) -> FeatureModel:
        return fm_utils.transform_tree(self.transformations, fm, self.features, copy_model)

    def __str__(self) -> str:
        return f'{self.type}{self.value}{[f for f in self.features]}'


def get_transformations_vector(constraints_order: tuple[list[Constraint], dict[int, tuple[int, int]]]) -> list[tuple[SimpleCTCTransformation, SimpleCTCTransformation]]:
    """Get the transformations vector from a specific constraints order."""
    transformations_vector = []
    for i, ctc in enumerate(constraints_order[0]):
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


def execute_transformations_vector(fm: FeatureModel, 
                                   transformations_vector: list[tuple[SimpleCTCTransformation, SimpleCTCTransformation]], 
                                   binary_vector: list[str]) -> tuple[FeatureModel, int]:
    """Execute a transformations vector according to the binary number of the vector provided.
    
    It returns the resulting model and the transformation (bit) that fails in case of a
    transformation returns NIL (None).
    """
    assert len(transformations_vector) == len(binary_vector)

    tree = FeatureModel(copy.deepcopy(fm.root))
    i = 0
    while i < len(transformations_vector) and tree is not None:
        tree = transformations_vector[i][int(binary_vector[i])].transforms(tree)
        i += 1
    return (tree, i-1)


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
    binary_vector[bit+1:] = ['0' for d in binary_vector[bit+1:]] 
    num = int(''.join(binary_vector), 2)
    if bit < 0:
        num = 2**len(binary_vector)
    return num


def get_valid_transformations_ids(fm: FeatureModel,
                                  transformations_vector: list[tuple[SimpleCTCTransformation, SimpleCTCTransformation]]) -> list[int]:
    n_bits = len(transformations_vector)
    #binary_vector = format(0, f'0{n_bits}b')
    num = 0
    i_bit = n_bits
    max = 2**n_bits
    valid_transformed_numbers_trees = []
    percentage = 0.0
    while num < max:
        #binary_vector = list(format(num, f'0{n_bits}b')[::-1])
        binary_vector = list(format(num, f'0{n_bits}b'))
        tree, null_bit = execute_transformations_vector(fm, transformations_vector, binary_vector)
        if tree is not None:
            #print(f'{num}: {"".join(binary_vector)} -> OK')
            valid_transformed_numbers_trees.append(num)
            num += 1
        else:  # tree is None
            print(f'Transformation resulted in NULL. Bit: {null_bit}')
            num = get_next_number_prunning_binary_vector(binary_vector, null_bit)
            #print(f'  |- next number: {num}')
        percentage = (num / max) * 100
        print(f'#Valid subtrees: {len(valid_transformed_numbers_trees)}. Num: {num} / {max} Ratio: ({percentage}%)')
    return valid_transformed_numbers_trees