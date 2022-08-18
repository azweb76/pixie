import os

from logging import getLogger

from . import utils


_log = getLogger(__name__)


class PixieConfig(dict):
    file: str

    @staticmethod
    def from_user():
        config_file = os.path.realpath(os.path.expanduser('~/.pixie/config.yaml'))
        config = PixieConfig.from_file(config_file)
        config.file = config_file
        return config

    def save_user(self):
        utils.save_yaml(dict(self), self.file)

    @staticmethod
    def from_file(file):
        _log.debug('reading config file %s', file)
        return PixieConfig(utils.read_yaml(file, {}))
