import json
from typing import Any 
from enum import Enum

from flamapy.core.models.ast import  ASTOperation
from flamapy.core.transformations import ModelToText

from flamapy.metamodels.fm_metamodel.models import  Feature, Attribute

from fm_solver.models import FMSans
from fm_solver.models.utils import TransformationsVector, SimpleCTCTransformation



class JSONFeatureType(Enum):
    FEATURE = 'FEATURE'
    XOR = 'XOR'
    OR = 'OR'
    MUTEX = 'MUTEX'
    CARDINALITY = 'CARDINALITY'
    OPTIONAL = 'OPTIONAL'
    MANDATORY = 'MANDATORY'


class FMSansWriter(ModelToText):

    CTC_TYPES = {ASTOperation.NOT: 'NotTerm',
                 ASTOperation.AND: 'AndTerm',
                 ASTOperation.OR: 'OrTerm',
                 ASTOperation.XOR: 'XorTerm',
                 ASTOperation.IMPLIES: 'ImpliesTerm',
                 ASTOperation.REQUIRES: 'RequiresTerm',
                 ASTOperation.EXCLUDES: 'ExcludesTerm',
                 ASTOperation.EQUIVALENCE: 'EquivalentTerm',
                 'FEATURE': 'FeatureTerm'}

    @staticmethod
    def get_destination_extension() -> str:
        return '.json'

    def __init__(self, path: str, source_model: FMSans) -> None:
        self.path = path
        self.source_model = source_model

    def transform(self) -> str:
        json_object = _to_json(self.source_model)
        if self.path is not None:
            with open(self.path, 'w', encoding='utf8') as file:
                json.dump(json_object, file, indent=4)
        return json.dumps(json_object, indent=4)


def _to_json(fm_sans: FMSans) -> dict[str, Any]:
    result: dict[str, Any] = {}
    #result['features_without_constraints'] = {} if fm_sans.subtree_without_constraints_implications is None else _get_tree_info(fm_sans.subtree_without_constraints_implications.root)
    #result['features_with_constraints'] = {} if fm_sans.subtree_with_constraints_implications is None else _get_tree_info(fm_sans.subtree_with_constraints_implications.root)
    result['feature_tree'] = {} if fm_sans.fm is None else _get_tree_info(fm_sans.fm.root)
    result['ctcs_transformations'] = [] if fm_sans.transformations_vector is None else _get_ctcs_transformations_info(fm_sans.transformations_vector)
    result['transformations_ids'] = {} if fm_sans.transformations_ids is None else fm_sans.transformations_ids
    return result


def _get_tree_info(feature: Feature) -> dict[str, Any]:
    feature_info = {}
    feature_info['name'] = feature.name
    feature_info['abstract'] = feature.is_abstract

    relations = []
    for relation in feature.get_relations():
        relation_info = {}
        relation_type = JSONFeatureType.FEATURE.value
        if relation.is_alternative():
            relation_type = JSONFeatureType.XOR.value
        elif relation.is_or():
            relation_type = JSONFeatureType.OR.value
        elif relation.is_mutex():
            relation_type = JSONFeatureType.MUTEX.value
        elif relation.is_cardinal():
            relation_type = JSONFeatureType.CARDINALITY.value
        elif relation.is_mandatory():
            relation_type = JSONFeatureType.MANDATORY.value
        elif relation.is_optional():
            relation_type = JSONFeatureType.OPTIONAL.value
        relation_info['type'] = relation_type
        relation_info['card_min'] = relation.card_min
        relation_info['card_max'] = relation.card_max
        children = []
        for child in relation.children:
            children.append(_get_tree_info(child))
        relation_info['children'] = children
        relations.append(relation_info)

    feature_info['relations'] = relations

    # Attributes
    feature_info['attributes'] = _get_attributes_info(feature.get_attributes())
    return feature_info


def _get_attributes_info(attributes: list[Attribute]) -> list[dict[str, Any]]:
    attributes_info = []
    for attribute in attributes:
        attr_info = {}
        attr_info['name'] = attribute.name
        if attribute.default_value is not None:
            attr_info['value'] = attribute.default_value
        attributes_info.append(attr_info)
    return attributes_info


def _get_ctcs_transformations_info(transformations_vector: TransformationsVector) -> list[dict[str, Any]]:
    info = []
    for tv in transformations_vector.transformations:
        tv_info = [_get_transformation_info(tv[0]), _get_transformation_info(tv[1])]
        info.append(tv_info)
    return info


def _get_transformation_info(transformation: SimpleCTCTransformation) -> dict[str, Any]:
    info = {}
    info['type'] = transformation.type
    info['value'] = transformation.value
    info['features'] = transformation.features
    return info
