from flamapy.core.transformations import ModelToModel
from flamapy.metamodels.fm_metamodel.models import FeatureModel, Constraint
from fm_solver.models import feature_model

from fm_solver.models.feature_model import FM
from fm_solver.models import FMSans, fm_sans
from fm_solver.models.utils import TransformationsVector
from fm_solver.transformations.fm_to_fmsans import FMToFMSans
from fm_solver.utils import utils, fm_utils
from fm_solver.transformations.refactorings import (
    RefactoringPseudoComplexConstraint,
    RefactoringStrictComplexConstraint
)

import csv
from time import process_time

class PicassoFMToFMSans(FMToFMSans):
    """Transform a feature model with cross-tree constraints to an equivalent
    feature model sans constraints (without any cross-tree constraints).
    
    The resulting feature model has the same semantics (i.e., same products) and 
    the same number of configurations.
    """

    @staticmethod
    def get_source_extension() -> str:
        return 'fm'

    @staticmethod
    def get_destination_extension() -> str:
        return 'fmsans'

    def __init__(self, source_model: feature_model,file_division:str,max_time:int,n_task) -> None:
         super().__init__(source_model, 1, n_task, 0, 0,1,1,max_time)
         self.file_division=file_division
         self.n_tasks


    def transform(self) -> FMSans:
         return picasso_fm_to_fmsans(self.feature_model, self.file_division,self.max_time,self.n_tasks)


def picasso_fm_to_fmsans(feature_model: FeatureModel, file_division:str,max_time:int,n_task:int) -> FMSans:
    fm = FM.from_feature_model(feature_model)

    if not fm.get_constraints():
        # The feature model has not any constraint.
        return FMSans(FM(fm.root), None, {})

    # Refactor pseudo-complex constraints
    fm = utils.apply_refactoring(fm, RefactoringPseudoComplexConstraint)
    # Refactor strict-complex constraints
    fm = utils.apply_refactoring(fm, RefactoringStrictComplexConstraint)

    # Get transformations vector
    trans_vector = TransformationsVector.from_constraints(fm.get_constraints())

      #Explore by divisions if a file is provided.
    min_max_current_task = []

   

    st = process_time()
    lines_2_delete=[]
    valid_transformed_numbers_trees={}
    with open(file_division, 'r+') as file:
        lines = file.readlines()
        contLine = 0
        while ((process_time()-st<max_time) and (contLine<len(lines))):
            
            for line in lines:
                line_division = line.split(";")
         
                #Medimos tiempo,
                
                
                newTrans = trans_vector.get_valid_transformations_ids_picassso(fm, n_task,int(line_division[0]), int(line_division[2]),int(line_division[3]),int(line_division[1]),max_time-(process_time()-st))
                if (len(newTrans)>0):
                    valid_transformed_numbers_trees.update(newTrans)
        
                lines_2_delete.append(contLine)
                # Remove a line by index
                contLine+=1
                if (process_time()-st>max_time):
                    break

        for l in reversed(lines_2_delete):
            del lines[l]
        # Write the modified content back to the file
        file.seek(0)  # Move the file pointer to the beginning
        file.truncate()
        file.writelines(lines)
        file.close()


            
        
    
    # Get FMSans instance
    return FMSans(FM(fm.root), trans_vector, valid_transformed_numbers_trees)


