from abc import ABC, abstractmethod

from flamapy.metamodels.fm_metamodel.models import FeatureModel

from fm_solver.models.utils import SimpleCTCTransformation, TransformationsVector


class Heuristic(ABC):

    def __init__(self, fm: FeatureModel) -> None:
        self.fm = fm
        self.constraints = fm.get_constraints() if fm is not None else None

    def name(self) -> str:
        pass

    def get_transformation_vector(self) -> TransformationsVector:
        return TransformationsVector(self.get_transformations())
        
    @abstractmethod
    def get_transformations(self) -> list[tuple[SimpleCTCTransformation, SimpleCTCTransformation]]:
        pass