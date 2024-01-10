import random

from flamapy.metamodels.fm_metamodel.models import Constraint

from fm_solver.models.utils import SimpleCTCTransformation, TransformationsVector
from fm_solver.transformations.heuristics import Heuristic
from fm_solver.utils import constraints_utils


class RandomHeuristic(Heuristic):

    def name(self) -> str:
        return "Random"

    def get_transformations(self) -> list[tuple[SimpleCTCTransformation, SimpleCTCTransformation]]:
        vector = []
        random.shuffle(self.constraints)
        for ctc in self.constraints:
            left_feature, right_feature = constraints_utils.left_right_features_from_simple_constraint(ctc)
            if constraints_utils.is_requires_constraint(ctc):
                t0 = SimpleCTCTransformation(SimpleCTCTransformation.REQUIRES, 0, SimpleCTCTransformation.REQUIRES_T0, [right_feature])
                t1 = SimpleCTCTransformation(SimpleCTCTransformation.REQUIRES, 1, SimpleCTCTransformation.REQUIRES_T1, [left_feature, right_feature])
            else:  # it is an excludes
                t0 = SimpleCTCTransformation(SimpleCTCTransformation.EXCLUDES, 0, SimpleCTCTransformation.EXCLUDES_T0, [right_feature])
                t1 = SimpleCTCTransformation(SimpleCTCTransformation.EXCLUDES, 1, SimpleCTCTransformation.EXCLUDES_T1, [left_feature, right_feature])
            trans_tuple = [t0, t1]
            random.shuffle(trans_tuple)
            vector.append(tuple(trans_tuple))
        return vector