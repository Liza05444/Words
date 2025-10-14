import os

import yaml


def read_version():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(current_dir, "..", "etc", "config.yaml")) as f:
        config = yaml.safe_load(f)
        return config["version"]


__appname__ = "kts_backend"
__version__ = read_version()
