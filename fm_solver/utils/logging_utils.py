import logging
import logging.config 
from typing import Any

import yaml


LOGGING_CONFIG_FILE = 'logging_config.yml'
MAIN_LOGGER_NAME = 'main_logger'
FM_LOGGER_NAME = 'fm_logger'


# Configure the logging module
def initialize_logging_config() -> dict[str, Any]:
    with open(LOGGING_CONFIG_FILE, 'r') as stream:
        config = yaml.load(stream, Loader=yaml.FullLoader)
    logging.config.dictConfig(config)
    return config
CONFIG = initialize_logging_config()


# Logger to be used across the application
LOGGER = logging.getLogger(MAIN_LOGGER_NAME)
LOGGER.disabled = CONFIG['loggers'][MAIN_LOGGER_NAME].get('disabled', False)
FM_LOGGER = logging.getLogger(FM_LOGGER_NAME)
LOGGER.disabled = CONFIG['loggers'][FM_LOGGER_NAME].get('disabled', False)
