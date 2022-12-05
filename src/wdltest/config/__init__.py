import os
from wdltest.constants import *
from wdltest.exception.wdl_test_cli_exit_exception import WdlTestCliExitException

class Config(object):

    _cli_kwargs = None
    _instance = None
    _configuration_parameters = [
        # WALLET
        {
            "attr": "wallet_url",
            "env": "WALLET_URL",
            "arg": None,
            "default": DEFAULT_WALLET_URL
        },
        {
            "attr": "wallet_client_id",
            "env": "WALLET_CLIENT_ID",
            "arg": None,
            "default": DEFAULT_WALLET_CLIENT_ID
        },
        {
            "attr": "wallet_client_secret",
            "env": "WALLET_CLIENT_SECRET",
            "arg": None,
            "default": None
        },
        # WORKBENCH EWES
        {
            "attr": "workbench_ewes_url",
            "env": "WORKBENCH_EWES_URL",
            "arg": None,
            "default": DEFAULT_WORKBENCH_EWES_URL
        },
        {
            "attr": "workbench_ewes_refresh_token",
            "env": "WORKBENCH_EWES_REFRESH_TOKEN",
            "arg": None,
            "default": None
        },
        # WORBENCH WORKFLOW SERVICE
        {
            "attr": "workbench_workflow_service_url",
            "env": "WORKBENCH_WORKFLOW_SERVICE_URL",
            "arg": None,
            "default": DEFAULT_WORKBENCH_WORKFLOW_SERVICE_URL
        },
        {
            "attr": "workbench_workflow_service_refresh_token",
            "env": "WORKBENCH_WORKFLOW_SERVICE_REFRESH_TOKEN",
            "arg": None,
            "default": None
        },
        {
            "attr": "all",
            "env": None,
            "arg": "all",
            "default": False
        }
    ]

    @classmethod
    def load(cls, cli_kwargs):
        if cls._instance is not None:
            raise WdlTestCliExitException("Cannot load Config, already loaded")
        
        cls._cli_kwargs = cli_kwargs
        cls._instance = cls.__new__(cls, cli_kwargs)

    @classmethod
    def instance(cls):
        if cls._instance is None:
            raise WdlTestCliExitException("Config not loaded, use load() frst")
        return cls._instance
    
    @classmethod
    def __eval(cls, env, arg, default):

        # attempt to load from environment variable
        if env and os.getenv(env):
            return os.getenv(env)
        
        # attempt to load from command line arg
        if arg and arg in cls._cli_kwargs.keys():
            return cls._cli_kwargs[arg]
        
        # load from default
        if default:
            return default

    def __new__(cls, cli_kwargs):
        config = super(Config, cls).__new__(cls)
        
        config.cli_kwargs = cli_kwargs

        for cp in cls._configuration_parameters:
            config.__setattr__(cp["attr"], cls.__eval(cp["env"], cp["arg"], cp["default"]))

        return config

    @property
    def workbench_ewes_refresh_token(self):
        return self._workbench_ewes_refresh_token
    
    @workbench_ewes_refresh_token.setter
    def workbench_ewes_refresh_token(self, workbench_ewes_refresh_token):
        self._workbench_ewes_refresh_token = workbench_ewes_refresh_token
