from flamapy.metamodels.fm_metamodel.models import FeatureModel, Constraint

from fm_solver.models.utils import SimpleCTCTransformation, TransformationsVector
from fm_solver.transformations.heuristics import Heuristic
from fm_solver.utils import fm_utils, constraints_utils
from fm_solver.utils.evaluate_transformation_vector import Evaluate_transformation_vector
import pickle
import os.path


class GeneticHeuristic(Heuristic):
    """
    TODO: TO UPDATE
    It performs a pre-analysis that takes into account the number of features to be removed 
    by the transformations required to refactor the constraint without executing the transformation
    over the model.
    """

    def name(self) -> str:
        return "Genetic"
    
    def get_transformations(self) -> list[tuple[SimpleCTCTransformation, SimpleCTCTransformation]]:
        # Order of the constraints:

        file_name="knowledge/"+str(self.fm.root.name)+".constraints.pkl"
        if (os.path.isfile(file_name)):
            with open(file_name, 'rb') as inp:
                data = pickle.load(inp)
        else:
            constraints_analysis = {}
            for i, ctc in enumerate(self.constraints):
                constraints_analysis[i] = fm_utils.numbers_of_features_to_be_removed(self.fm, ctc)
            # Order by best transformation
            constraints_ordered = dict(sorted(constraints_analysis.items(), key=lambda item: max(item[1][0], item[1][1]), reverse=True))  

            new_trans_vector_p = Evaluate_transformation_vector.best_order(self.constraints)

            #new_trans_vector_o=Evaluate_transformation_vector.reorder(self.constraints,new_trans_vector_p,constraints_ordered)
            
            data = self.constraints
            #data = [data[i] for i in new_trans_vector_o]
            data = [data[i] for i in new_trans_vector_p]
            with open(file_name, 'wb') as inp:
                pickle.dump(data,inp, pickle.HIGHEST_PROTOCOL)

        self.constraints = data

        vector = []
        for ctc in self.constraints:
            left_feature, right_feature = constraints_utils.left_right_features_from_simple_constraint(ctc)
            if constraints_utils.is_requires_constraint(ctc):
                t0 = SimpleCTCTransformation(SimpleCTCTransformation.REQUIRES, 0, SimpleCTCTransformation.REQUIRES_T0, [right_feature])
                t1 = SimpleCTCTransformation(SimpleCTCTransformation.REQUIRES, 1, SimpleCTCTransformation.REQUIRES_T1, [left_feature, right_feature])
            else:  # it is an excludes
                t0 = SimpleCTCTransformation(SimpleCTCTransformation.EXCLUDES, 0, SimpleCTCTransformation.EXCLUDES_T0, [right_feature])
                t1 = SimpleCTCTransformation(SimpleCTCTransformation.EXCLUDES, 1, SimpleCTCTransformation.EXCLUDES_T1, [left_feature, right_feature])
            transformation_tuple = (t0, t1)
            vector.append(transformation_tuple)
        return vector
    