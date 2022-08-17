import os

from pixie import utils


class PixieConfig(dict):
    __file: str

    @staticmethod
    def from_user():
        config_file = os.path.realpath(os.path.expanduser('~/.pixie/config.yaml'))
        config = PixieConfig.from_file(config_file)
        config.__file = config_file
        return config

    def save_user(self):
        utils.save_yaml(self, self.__file)

    @staticmethod
    def from_file(file):
        return PixieConfig(utils.read_yaml(file, {}))