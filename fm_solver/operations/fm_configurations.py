import copy
import itertools

from flamapy.metamodels.configuration_metamodel.models import Configuration
from flamapy.metamodels.fm_metamodel.models import FeatureModel, Feature

from fm_solver.operations import FMOperation


class FMConfigurations(FMOperation):
    """It computes the configurations of the feature model."""

    @staticmethod
    def get_name() -> str:
        return 'Configurations number'

    def __init__(self) -> None:
        self._result = 0
        self.feature_model = None

    def execute(self, model: FeatureModel) -> 'FMConfigurations':
        self.feature_model = model
        self._result = self.get_configurations()
        return self

    def get_result(self) -> list[Configuration]:
        return self._result

    def get_configurations(self) -> list[Configuration]:
        return configurations_rec(self.feature_model, self.feature_model.root)


def configurations_rec(fm: FeatureModel, feature: Feature) -> list[Configuration]:
    original_feature = get_original_feature(fm, feature)
    feature_config = Configuration(elements={original_feature: True})
    if feature.is_leaf():
        return [feature_config]
    all_configs = []
    for relation in feature.get_relations():
        if relation.is_mandatory():
            sub_configs = configurations_rec(fm, relation.children[0])
            configs = add_feature_to_configurations(original_feature, sub_configs)
            if not all_configs:
                all_configs.extend(configs)
            else:
                new_configs = []
                for c in configs:
                    copy_all_configs = copy.deepcopy(all_configs)
                    new_configs.extend(add_configurations_to_configurations([c], copy_all_configs))
                all_configs = new_configs
        elif relation.is_optional():
            sub_configs = configurations_rec(fm, relation.children[0])
            configs = add_feature_to_configurations(original_feature, sub_configs)
            configs.append(feature_config)
            if not all_configs:
                all_configs.extend(configs)
            else:
                copy_all_configs = copy.deepcopy(all_configs)
                all_configs = add_configurations_to_configurations(configs, all_configs)
                all_configs.extend(copy_all_configs)
        elif relation.is_alternative():
            configs = []
            for child in relation.children:
                sub_configs = configurations_rec(fm, child)
                sub_configs = add_feature_to_configurations(original_feature, sub_configs)
                configs.extend(sub_configs)
            all_configs.extend(configs)
        elif relation.is_or():
            configs_dict: dict[Feature, list[Configuration]] = dict()
            for child in relation.children:
                sub_configs = configurations_rec(fm, child)
                sub_configs = add_feature_to_configurations(original_feature, sub_configs)
                configs_dict[child] = sub_configs
            
            configs = []
            for size in range(1, len(relation.children) + 1):
                combinations = itertools.combinations(relation.children, size)
                for combi in combinations:
                    configs_combi = []
                    for child in combi:
                        configs_combi = add_configurations_to_configurations(copy.deepcopy(configs_dict[child]), configs_combi)
                    configs.extend(configs_combi)
            all_configs.extend(configs)
    return all_configs


def add_feature_to_configurations(feature: Feature, configurations: list[Configuration]) -> list[Configuration]:
    for config in configurations:
        config.elements.update({feature: True})
    return configurations


def add_configurations_to_configurations(new_configurations: list[Configuration], configurations: list[Configuration]) -> list[Configuration]:
    if not configurations:
        return new_configurations
    for config in configurations:
        for new_c in new_configurations:
            config.elements.update(new_c.elements)
    return configurations


def get_original_feature(fm: FeatureModel, feature: Feature) -> Feature:
    ref_attribute = next((a for a in feature.get_attributes() if a.name == 'ref'), None)
    if ref_attribute is None:
        original_feature = feature
    else:
        original_feature = fm.get_feature_by_name(ref_attribute.get_default_value())
    return original_feature