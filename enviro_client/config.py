# TODO: Copy packaged config to config dir (using appdirs) to use as defaults
from pathlib import Path

from yaml import safe_load

CONFIG_FILE = Path(__file__).parent.parent / 'enviro.yml'


def load_config():
    with open(CONFIG_FILE) as f:
        return safe_load(f)
