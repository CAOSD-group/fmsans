from collections.abc import Callable

from flamapy.metamodels.fm_metamodel.models import FeatureModel

from fm_solver.utils import fm_utils


class SimpleCTCTransformation():
    """It represents a transformation of a simple cross-tree constraint (requires or excludes).

    It contains:
        - a name being 'R' for requires constraints, and 'E' for excludes constraints.
        - a value being 0 for the first transformation and 1 for the second transformation.
        - a list of functions that implement the transformation.
        - a list of features (the features of the constraint) to which the transformation will be applied.
    """
    REQUIRES = 'R'
    EXCLUDES = 'E'

    def __init__(self, name: str, value: int, transformations: list[Callable], features: list[str]) -> None:
        self.name = name
        self.value = value
        self.transformations = transformations
        self.features = features

    def transforms(self, fm: FeatureModel, copy_model: bool = False) -> FeatureModel:
        return fm_utils.transform_tree(self.transformations, fm, self.features, copy_model)

    def __str__(self) -> str:
        return f'{self.name}{self.value}{[f for f in self.features]}'


def execute_transformations_vector(fm: FeatureModel, 
                                   transformations_vector: list[tuple[SimpleCTCTransformation, SimpleCTCTransformation]], 
                                   binary_vector: list[str]) -> tuple[FeatureModel, int]:
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
