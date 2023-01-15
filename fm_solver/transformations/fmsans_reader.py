import json
from typing import Any 

from flamapy.core.transformations import TextToModel

from flamapy.metamodels.fm_metamodel.models import (
    Relation, 
    Feature, 
    Attribute
)

from fm_solver.models.feature_model import FM
from fm_solver.models import FMSans, SimpleCTCTransformation
from fm_solver.transformations import JSONFeatureType


class FMSansReader(TextToModel):

    @staticmethod
    def get_source_extension() -> str:
        return '.json'

    def __init__(self, path: str) -> None:
        self.path = path

    def transform(self) -> FMSans:
        fm_sans = None
        with open(self.path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            fm_sans = FMSansReader.parse_json(data)
        return fm_sans

    @staticmethod
    def parse_json(data: str) -> FMSans:
        features_without_constraints_info = data['features_without_constraints']
        features_with_constraints_info = data['features_with_constraints']
        ctcs_transformations_info = data['ctcs_transformations']
        transformations_ids = data['transformations_ids']

        subtree_without_constraints_implications = None if not features_without_constraints_info else FM(parse_tree(None, features_without_constraints_info))
        subtree_with_constraints_implications = None if not features_with_constraints_info else FM(parse_tree(None, features_with_constraints_info))
        transformations_vector = None if not ctcs_transformations_info else parse_ctcs_transformations(ctcs_transformations_info)
        transformations_ids = None if not transformations_ids else {h: int(i) for h, i in transformations_ids.items()}
        return FMSans(subtree_with_constraints_implications=subtree_with_constraints_implications,
                      subtree_without_constraints_implications=subtree_without_constraints_implications,
                      transformations_vector=transformations_vector,
                      transformations_ids=transformations_ids)


def parse_tree(parent: Feature, feature_node: dict[str, Any]) -> Feature:
    """Parse the tree structure and returns the root feature."""
    feature_name = feature_node['name']
    is_abstract = feature_node['abstract']
    feature = Feature(name=feature_name, parent=parent, is_abstract=is_abstract)

    # Attributes
    if 'attributes' in feature_node:
        for attribute in feature_node['attributes']:
            attribute_name = attribute['name']
            if 'value' in attribute:
                attribute_value = attribute['value']
            else:
                attribute_value = None
            attr = Attribute(attribute_name, None, attribute_value, None)
            attr.set_parent(feature)
            feature.add_attribute(attr)

    if 'relations' in feature_node:
        for relation in feature_node['relations']:
            children = []
            for child in relation['children']:
                child_feature = parse_tree(feature, child)
                children.append(child_feature)
            relation_type = relation['type']
            if relation_type == JSONFeatureType.OPTIONAL.value:
                new_relation = Relation(feature, children, 0, 1)
            elif relation_type == JSONFeatureType.MANDATORY.value:
                new_relation = Relation(feature, children, 1, 1)
            elif relation_type == JSONFeatureType.XOR.value:
                new_relation = Relation(feature, children, 1, 1)
            elif relation_type == JSONFeatureType.OR.value:
                new_relation = Relation(feature, children, 1, len(children))
            elif relation_type == JSONFeatureType.MUTEX.value:
                new_relation = Relation(feature, children, 0, 1)
            elif relation_type == JSONFeatureType.CARDINALITY.value:  # Group Cardinality
                card_min = relation['card_min']
                card_max = relation['card_max']
                new_relation = Relation(feature, children, card_min, card_max)
            feature.add_relation(new_relation)
    return feature


def parse_ctcs_transformations(ctcs_transformations_info: list[dict[str, Any]]) -> list[tuple[SimpleCTCTransformation, SimpleCTCTransformation]]:
    transformations_vector = []
    for ct_info in ctcs_transformations_info:
        t0 = parse_simple_transformation(ct_info[0])
        t1 = parse_simple_transformation(ct_info[1])
        transformations_vector.append((t0, t1))
    return transformations_vector


def parse_simple_transformation(transformation_info: dict[str, Any]) -> SimpleCTCTransformation:
    type = transformation_info['type']
    value = transformation_info['value']
    features = transformation_info['features']
    if type == SimpleCTCTransformation.REQUIRES:
        transformations = SimpleCTCTransformation.REQUIRES_T0 if value == 0 else SimpleCTCTransformation.REQUIRES_T1
    else:
        transformations = SimpleCTCTransformation.EXCLUDES_T0 if value == 0 else SimpleCTCTransformation.EXCLUDES_T1
    return SimpleCTCTransformation(type, value, transformations, features)
