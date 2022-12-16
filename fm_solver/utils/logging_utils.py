import logging
import logging.config 

import yaml

from flamapy.metamodels.fm_metamodel.models import FeatureModel

from fm_solver.models import FMSans, SimpleCTCTransformation
from fm_solver.utils import constraints_utils, config_utils


# Configure the logging module
def initialize_logging_config() -> None:
    with open(config_utils.LOGGING_CONFIG_FILE, 'r') as stream:
        config = yaml.load(stream, Loader=yaml.FullLoader)
        print("Initialize logging config")
    logging.config.dictConfig(config)
initialize_logging_config()


# Logger to be used across the application
LOGGER = logging.getLogger(config_utils.MAIN_LOGGER)
FM_LOGGER = logging.getLogger(config_utils.FM_LOGGER)


# Utils functions:
def fm_stats(fm: FeatureModel) -> str:
    lines = []
    lines.append(f'FM stats:')
    lines.append(f'  #Features:       {len(fm.get_features())}')
    lines.append(f'  #Relations:      {len(fm.get_relations())}')
    lines.append(f'  #Constraints:    {len(fm.get_constraints())}')
    lines.append(f'    #Simple CTCs:  {len([ctc for ctc in fm.get_constraints() if constraints_utils.is_simple_constraint(ctc)])}')
    lines.append(f'      #Requires:   {len([ctc for ctc in fm.get_constraints() if constraints_utils.is_requires_constraint(ctc)])}')
    lines.append(f'      #Excludes:   {len([ctc for ctc in fm.get_constraints() if constraints_utils.is_excludes_constraint(ctc)])}')
    lines.append(f'    #Complex CTCs: {len([ctc for ctc in fm.get_constraints() if constraints_utils.is_complex_constraint(ctc)])}')
    return '\n'.join(lines)


def fmsans_stats(fm: FMSans) -> str:
    features_without_implications = 0 if fm.subtree_without_constraints_implications is None else len(fm.subtree_without_constraints_implications.get_features())
    features_with_implications = 0 if fm.subtree_with_constraints_implications is None else len(fm.subtree_with_constraints_implications.get_features())
    constraints = 0 if fm.transformations_vector is None else len(fm.transformations_vector)
    requires_ctcs = 0 if fm.transformations_vector is None else len([ctc for ctc in fm.transformations_vector if ctc[0].type == SimpleCTCTransformation.REQUIRES])
    excludes_ctcs = 0 if fm.transformations_vector is None else len([ctc for ctc in fm.transformations_vector if ctc[0].type == SimpleCTCTransformation.EXCLUDES])
    subtrees = 0 if fm.transformations_ids is None else len(fm.transformations_ids)
    lines = []
    lines.append(f'FMSans stats:')
    lines.append(f'  #Features:            {features_without_implications + features_with_implications}')
    lines.append(f'    #Features out CTCs: {features_without_implications}')
    lines.append(f'    #Features in CTCs:  {features_with_implications}')
    lines.append(f'  #Constraints:         {constraints}')
    lines.append(f'    #Requires:          {requires_ctcs}')
    lines.append(f'    #Excludes:          {excludes_ctcs}')
    lines.append(f'  #Subtrees:            {subtrees}')
    return '\n'.join(lines)