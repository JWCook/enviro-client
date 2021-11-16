# TODO: Copy packaged config to config dir (using appdirs) to use as defaults
from copy import deepcopy
from pathlib import Path

from loguru import logger
from yaml import safe_load

CONFIG_FILE = Path(__file__).parent.parent / 'enviro.yml'


def load_config():
    with open(CONFIG_FILE) as f:
        config = safe_load(f)

    msg_config = deepcopy(config)
    if msg_config['mqtt'].get('password'):
        msg_config['mqtt']['password'] = '**********'
    logger.debug(f'Loaded config: {msg_config}')

    return config
