import copy
from typing import Any
from collections.abc import Callable

from flamapy.metamodels.fm_metamodel.models import (
    FeatureModel, 
    Feature, 
    Relation, 
    Constraint, 
    Attribute
)

from fm_solver.utils import fm_utils, constraints_utils, logging_utils, timer

from fm_solver.transformations.refactorings import RefactoringPseudoComplexConstraint
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
        max = len(self.transformations_ids)
        for i, num in enumerate(self.transformations_ids):
            binary_vector = list(format(num, f'0{n_bits}b'))
            tree, _ = execute_transformations_vector(self.subtree_with_constraints_implications, self.transformations_vector, binary_vector)
            subtrees.add(tree)
            percentage = (i / max) * 100
            logging_utils.LOGGER.debug(f'ID: {num}. {i} / {max} ({percentage}%)')
        # Join all subtrees
        logging_utils.LOGGER.debug(f'Getting full model from {len(subtrees)} unique subtrees...')
        result_fm = fm_utils.get_model_from_subtrees(self.subtree_with_constraints_implications, subtrees)
        # Mix result FM and subtree without implications:
        # 1. Change name to the original root
        if self.subtree_without_constraints_implications is None:
            fm = result_fm
        else:
            logging_utils.LOGGER.debug(f'Joining subtrees to subtree without CTCs implications...')
            #self.subtree_without_constraints_implications.root.name = fm_utils.get_new_feature_name(result_fm, 'Root')  # This is not needed.
            new_root = Feature(fm_utils.get_new_feature_name(result_fm, 'Root'), is_abstract=True)  # We can use the same feature's name for Root.
            #new_root = Feature(result_fm.root.name, is_abstract=True)   # We may use the same feature's name for Root.
            new_root.add_attribute(Attribute(name='new', domain=None, default_value=None, null_value=None))
            new_root.add_relation(Relation(new_root, [self.subtree_without_constraints_implications.root], 1, 1))
            self.subtree_without_constraints_implications.root.parent = new_root
            new_root.add_relation(Relation(new_root, [result_fm.root], 1, 1))
            result_fm.root.parent = new_root

            fm = FeatureModel(new_root)
        logging_utils.LOGGER.debug(f'Removing {sum(f.is_abstract for f in fm.get_features())} abstract features...')
        with timer.Timer(logger=logging_utils.LOGGER.info, message="Removing abstract features."): 
            fm = fm_utils.remove_leaf_abstract_features(fm)
        return fm

    def get_analysis(self) -> dict[str, Any]:
        if self.subtree_with_constraints_implications is None:
            return FMFullAnalysis().execute(self.subtree_without_constraints_implications).get_result()
        n_bits = len(self.transformations_vector)
        max = len(self.transformations_ids)
        results: list[dict[str, Any]] = []
        for i, num in enumerate(self.transformations_ids):
            binary_vector = list(format(num, f'0{n_bits}b'))
            tree, _ = execute_transformations_vector(self.subtree_with_constraints_implications, self.transformations_vector, binary_vector)
            analysis_result = FMFullAnalysis().execute(tree).get_result()
            results.append(analysis_result)
            percentage = (i / max) * 100
            logging_utils.LOGGER.debug(f'ID: {num}. {i} / {max} ({percentage}%)')
        # Join all subtrees
        for op, res in analysis_result.items():
            print(f'{op}: {res}')
        logging_utils.LOGGER.debug(f'Joining results from {max} unique subtrees...')
        result_subtree_without_constraints = FMFullAnalysis().execute(self.subtree_without_constraints_implications).get_result()
        for op, res in result_subtree_without_constraints.items():
            print(f'{op}: {res}')
        results.append(result_subtree_without_constraints)
        return FMFullAnalysis.join_results(results)
        

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
    num = 0
    max = 2**n_bits
    valid_transformed_numbers_trees = []
    percentage = 0.0
    total_invalids = 0
    total_skipped = 0
    while num < max:
        #binary_vector = list(format(num, f'0{n_bits}b')[::-1])
        binary_vector = list(format(num, f'0{n_bits}b'))
        tree, null_bit = execute_transformations_vector(fm, transformations_vector, binary_vector)
        if tree is not None:
            valid_transformed_numbers_trees.append(num)
            logging_utils.LOGGER.debug(f'ID (valid): {num} / {max} ({percentage}%), #Valids: {len(valid_transformed_numbers_trees)}')
            num += 1
        else:  # tree is None
            previous_num = num
            total_invalids += 1
            num = get_next_number_prunning_binary_vector(binary_vector, null_bit)
            skipped = num - previous_num - 1
            total_skipped += skipped
            logging_utils.LOGGER.debug(f'ID (not valid): {previous_num} / {max} ({percentage}%), null_bit: {null_bit}, {skipped} skipped. #Valids: {len(valid_transformed_numbers_trees)}')
        percentage = (num / max) * 100
    logging_utils.LOGGER.debug(f'Total IDs: {max}, #Valids: {len(valid_transformed_numbers_trees)}, #Invalids: {total_invalids}, #Skipped: {total_skipped}.')
    return valid_transformed_numbers_trees


def fm_stats(fm: FeatureModel) -> str:
    lines = []
    unique_features = [f for f in fm.get_features() if not any(a.name == 'ref' for a in f.get_attributes())]
    subtree_with_constraints_implications, subtree_without_constraints_implications = fm_utils.get_subtrees_constraints_implications(fm)
    features_without_implications = 0 if subtree_without_constraints_implications is None else len(subtree_without_constraints_implications.get_features())
    features_with_implications = 0 if subtree_with_constraints_implications is None else len(subtree_with_constraints_implications.get_features())
    complex_ctcs = len([ctc for ctc in fm.get_constraints() if constraints_utils.is_complex_constraint(ctc)])
    pseudo_complex_ctcs = len(RefactoringPseudoComplexConstraint.get_instances(fm))
    strict_complex_ctcs = complex_ctcs - pseudo_complex_ctcs
    lines.append(f'FM stats:')
    lines.append(f'  #Features:            {len(fm.get_features())}')
    lines.append(f'    #Unique Features:   {len(unique_features)}')
    lines.append(f'    #Features out CTCs: {features_without_implications}')
    lines.append(f'    #Features in CTCs:  {features_with_implications}')
    lines.append(f'  #Relations:           {len(fm.get_relations())}')
    lines.append(f'  #Constraints:         {len(fm.get_constraints())}')
    lines.append(f'    #Simple CTCs:       {len([ctc for ctc in fm.get_constraints() if constraints_utils.is_simple_constraint(ctc)])}')
    lines.append(f'      #Requires:        {len([ctc for ctc in fm.get_constraints() if constraints_utils.is_requires_constraint(ctc)])}')
    lines.append(f'      #Excludes:        {len([ctc for ctc in fm.get_constraints() if constraints_utils.is_excludes_constraint(ctc)])}')
    lines.append(f'    #Complex CTCs:      {complex_ctcs}')
    lines.append(f'      #Pseudo CTCs:      {pseudo_complex_ctcs}')
    lines.append(f'      #Strict CTCs:      {strict_complex_ctcs}')
    return '\n'.join(lines)


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