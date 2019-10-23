import logging
from pathlib import Path

import yaml

logger = logging.getLogger('aletheia')


confdir = Path('~').expanduser() / '.aletheia'
cachedir = confdir / 'data'

cachedir.mkdir(parents=True, exist_ok=True)

defaults = {'cache_dir': cachedir, 'conf_file': confdir / 'config.yaml', 'logging': 'INFO'}

conf = {}


def reset_conf():
    """Set conf values back to defaults"""
    conf.clear()
    conf.update(defaults)


def save_conf(fn=None):
    """Save current configuration to file as YAML"""

    if fn is None:
        fn = conf['conf_file']

    with open(fn, 'w') as f:
        yaml.dump(conf, f)


def load_conf(fn=None):
    """ Update global config from YAML file"""
    if fn is None:
        fn = conf['conf_file']
    if Path(fn).is_file():
        with open(fn) as f:
            try:
                conf.update(yaml.safe_load(f))
            except Exception as e:
                logger.warning('Failure to load config file "{fn}": {e}' ''.format(fn=fn, e=e))


def reload_all():
    reset_conf()
    load_conf()


reload_all()

logger.setLevel(conf['logging'].upper())
ch = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - '
    '%(filename)s:%(funcName)s:L%(lineno)d - '
    '%(message)s'
)
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.debug('Aletheia logger set to debug')
