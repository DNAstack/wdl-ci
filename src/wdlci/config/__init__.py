import json
from wdlci.config.config_file import ConfigFile
from wdlci.config.config_env import ConfigEnv
from wdlci.exception.wdl_test_cli_exit_exception import WdlTestCliExitException
from wdlci.constants import CONFIG_JSON


class ConfigEncoder(json.JSONEncoder):
    def default(self, o):
        return o.__dict__


class Config(object):
    _cli_kwargs = None
    _instance = None

    @classmethod
    def __new__(cls, cli_kwargs, initialize):
        file = ConfigFile.__new__(initialize=initialize)
        env = ConfigEnv.__new__(cli_kwargs)
        instance = super(Config, cls).__new__(cls)
        instance.__init__(file, env)

        return instance

    @classmethod
    def load(cls, cli_kwargs, initialize=False):
        if cls._instance is not None:
            raise WdlTestCliExitException("Cannot load Config, already loaded", 1)

        cls._cli_kwargs = cli_kwargs
        cls._instance = cls.__new__(cli_kwargs, initialize=initialize)

    @classmethod
    def instance(cls):
        if cls._instance is None:
            raise WdlTestCliExitException("Config not loaded, use load() first")
        return cls._instance

    def write(self):
        with open(CONFIG_JSON, "w") as f:
            json.dump(self.file, f, cls=ConfigEncoder, indent=2)

    def __init__(self, file, env):
        self._file = file
        self._env = env

    @property
    def file(self):
        return self._file

    @property
    def env(self):
        return self._env
