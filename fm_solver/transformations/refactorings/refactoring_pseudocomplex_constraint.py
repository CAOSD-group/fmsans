from flamapy.core.models import AST, ASTOperation
from flamapy.core.models import ast as ast_utils
from flamapy.metamodels.fm_metamodel.models import FeatureModel, Constraint

from fm_solver.transformations.refactorings import FMRefactoring


class RefactoringPseudoComplexConstraint(FMRefactoring):

    @staticmethod
    def get_name() -> str:
        return 'Pseudo-complex constraint refactoring'

    @staticmethod
    def get_description() -> str:
        return ("It splits a pseudo-complex constraint in multiple constraints dividing it "
                "by the AND operator when possible.")

    @staticmethod
    def get_language_construct_name() -> str:
        return 'Pseudo-complex constraint'

    @staticmethod
    def get_instances(model: FeatureModel) -> list[Constraint]:
        # TODO: re-implement for efficiency
        return [ctc for ctc in model.get_constraints() if len(split_constraint(ctc)) > 1]

    @staticmethod
    def is_applicable(model: FeatureModel) -> bool:
        # TODO: re-implement for efficiency
        return len(RefactoringPseudoComplexConstraint.get_instances(model)) > 0

    @staticmethod
    def transform(model: FeatureModel, instance: Constraint) -> FeatureModel:
        model.ctcs.remove(instance)
        for ctc in split_constraint(instance):
            model.ctcs.append(ctc)
        return model


def split_constraint(constraint: Constraint) -> list[Constraint]:
    """Given a constraint, split it in multiple constraints separated by the AND operator."""
    asts = split_formula(constraint.ast)
    asts_simplified = [ast_utils.simplify_formula(ast) for ast in asts]
    asts = []
    for ctc in asts_simplified:
        asts.extend(split_formula(ctc))
        
    asts_negation_propagated = [ast_utils.propagate_negation(ast.root) for ast in asts]
    asts = []
    for ctc in asts_negation_propagated:
        asts.extend(split_formula(ctc))

    asts_cnf = [ast_utils.to_cnf(ast) for ast in asts]
    asts = []
    for ctc in asts_cnf:
        asts.extend(split_formula(ctc))
    return [Constraint(f'{constraint.name}{i}', ast) for i, ast in enumerate(asts)]


def split_formula(formula: AST) -> list[AST]:
    """Given a formula, returns a list of formulas separated by the AND operator."""
    res = []
    node = formula.root
    if node.data == ASTOperation.AND:
        res.extend(split_formula(AST(node.left)))
        res.extend(split_formula(AST(node.right)))
    else:
        res.append(formula)
    return res