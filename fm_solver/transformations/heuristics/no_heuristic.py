from flamapy.metamodels.fm_metamodel.models import Constraint

from fm_solver.models.utils import SimpleCTCTransformation, TransformationsVector
from fm_solver.transformations.heuristics import Heuristic
from fm_solver.utils import constraints_utils


class NoHeuristic(Heuristic):

    def name(self) -> str:
        return "Normal"
    
    def get_transformations(self) -> list[tuple[SimpleCTCTransformation, SimpleCTCTransformation]]:
        vector = []
        for ctc in self.constraints:
            left_feature, right_feature = constraints_utils.left_right_features_from_simple_constraint(ctc)
            if constraints_utils.is_requires_constraint(ctc):
                t0 = SimpleCTCTransformation(SimpleCTCTransformation.REQUIRES, 0, SimpleCTCTransformation.REQUIRES_T0, [right_feature])
                t1 = SimpleCTCTransformation(SimpleCTCTransformation.REQUIRES, 1, SimpleCTCTransformation.REQUIRES_T1, [left_feature, right_feature])
            else:  # it is an excludes
                t0 = SimpleCTCTransformation(SimpleCTCTransformation.EXCLUDES, 0, SimpleCTCTransformation.EXCLUDES_T0, [right_feature])
                t1 = SimpleCTCTransformation(SimpleCTCTransformation.EXCLUDES, 1, SimpleCTCTransformation.EXCLUDES_T1, [left_feature, right_feature])
            vector.append((t0, t1))
        return vector