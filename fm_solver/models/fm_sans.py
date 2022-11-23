from flamapy.metamodels.fm_metamodel.models import FeatureModel


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

    def __init__(self, fm: FeatureModel) -> None:
        self._original_fm = fm
        self._transformation_vector = None  # Order of the transformations of the constraints
        self._transformations_ids = []  # Numbers of the transformations
