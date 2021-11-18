from copy import deepcopy
from pathlib import Path

from loguru import logger
from yaml import safe_load

CONFIG_FILE = Path('~/.config/enviro.yml').expanduser()
DEFAULT_CONFIG = {
    'display': {'enabled': True, 'interval': 0.25},
    'mqtt': {'enabled': False},
}


def load_config() -> dict:
    if not CONFIG_FILE.is_file():
        logger.warning(f'Config file {CONFIG_FILE} not found')
        return DEFAULT_CONFIG

    with open(CONFIG_FILE) as f:
        config = safe_load(f)

    # Redact creds before logging config
    msg_config = deepcopy(config)
    if msg_config['mqtt'].get('password'):
        msg_config['mqtt']['password'] = '********'
    logger.debug(f'Loaded config: {msg_config}')

    return config
