import json
from os import path

from my_custom_library import parameters


def load_configuration() -> any:
    """
    Load the configuration file for the bundle target.
    """
    config_file_path = path.join(
        parameters.bundle_file_path(), "config", f"{parameters.bundle_target()}.json"
    )
    with open(config_file_path, "r") as file:
        return json.load(file)
