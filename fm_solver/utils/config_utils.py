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
    return config
CONFIG = initialize_global_config()


# Global parameters to be used across the application
TIMER_ENABLED = CONFIG.get('timer_enabled', False)
SIZER_ENABLED = CONFIG.get('sizer_enabled', False)