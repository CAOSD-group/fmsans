from flamapy.metamodels.fm_metamodel.models import FeatureModel, Constraint

from fm_solver.models.utils import SimpleCTCTransformation, TransformationsVector
from fm_solver.transformations.heuristics import Heuristic
from fm_solver.utils import fm_utils, constraints_utils


class FeaturesRemovedHeuristic(Heuristic):
    """
    It performs a pre-analysis that takes into account the number of features to be removed 
    by the transformations required to refactor the constraint without executing the transformation
    over the model.
    """

    def get_transformations(self) -> list[tuple[SimpleCTCTransformation, SimpleCTCTransformation]]:
        # Order of the constraints:
        constraints_analysis = {}
        for i, ctc in enumerate(self.constraints):
            constraints_analysis[i] = fm_utils.numbers_of_features_to_be_removed(self.fm, ctc)
        # Order by best transformation
        constraints_ordered = dict(sorted(constraints_analysis.items(), key=lambda item: max(item[1][0], item[1][1]), reverse=True))  

        vector = []
        for i, v in constraints_ordered.items():
            left_feature, right_feature = constraints_utils.left_right_features_from_simple_constraint(self.constraints[i])
            if constraints_utils.is_requires_constraint(self.constraints[i]):
                t0 = SimpleCTCTransformation(SimpleCTCTransformation.REQUIRES, 0, SimpleCTCTransformation.REQUIRES_T0, [right_feature])
                t1 = SimpleCTCTransformation(SimpleCTCTransformation.REQUIRES, 1, SimpleCTCTransformation.REQUIRES_T1, [left_feature, right_feature])
            else:  # it is an excludes
                t0 = SimpleCTCTransformation(SimpleCTCTransformation.EXCLUDES, 0, SimpleCTCTransformation.EXCLUDES_T0, [right_feature])
                t1 = SimpleCTCTransformation(SimpleCTCTransformation.EXCLUDES, 1, SimpleCTCTransformation.EXCLUDES_T1, [left_feature, right_feature])
            transformation_tuple = (t0, t1) if constraints_ordered[i][0] >= constraints_ordered[i][1] else (t1, t0)
            vector.append(transformation_tuple)
        return vector
    