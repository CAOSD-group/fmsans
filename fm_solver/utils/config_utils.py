"""
This module contains the global configuration of the application based on a YAML configuration file.
"""
import yaml
from typing import Any


# Main configuration file
CONFIG_FILE = 'config.yml'


# Load the main (global) configuration of the application
def initialize_global_config() -> dict[str, Any]:
    with open(CONFIG_FILE, 'r') as stream:
        config = yaml.load(stream, Loader=yaml.FullLoader)
        print("Initialize global config")
    return config
CONFIG = initialize_global_config()


# Global parameters to be used across the application
MAIN_LOGGER = CONFIG['loggers']['main_logger']['name']
FM_LOGGER = CONFIG['loggers']['fm_logger']['name']
LOGGING_CONFIG_FILE = CONFIG['config_logging_file']