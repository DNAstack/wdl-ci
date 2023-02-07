import os
from wdlci.constants import *
from wdlci.exception.wdl_test_cli_exit_exception import WdlTestCliExitException


class ConfigEnv(object):

    _cli_kwargs = None
    _configuration_parameters = [
        # WALLET
        {
            "attr": "wallet_url",
            "env": "WALLET_URL",
            "arg": None,
            "default": DEFAULT_WALLET_URL,
        },
        {
            "attr": "wallet_client_id",
            "env": "WALLET_CLIENT_ID",
            "arg": None,
            "default": DEFAULT_WALLET_CLIENT_ID,
        },
        {
            "attr": "wallet_client_secret",
            "env": "WALLET_CLIENT_SECRET",
            "arg": None,
            "default": None,
        },
        # WORKBENCH
        {
            "attr": "workbench_namespace",
            "env": "WORKBENCH_NAMESPACE",
            "arg": None,
            "default": None,
        },
        # WORKBENCH EWES
        {
            "attr": "workbench_ewes_url",
            "env": "WORKBENCH_EWES_URL",
            "arg": None,
            "default": DEFAULT_WORKBENCH_EWES_URL,
        },
        {
            "attr": "workbench_ewes_refresh_token",
            "env": "WORKBENCH_EWES_REFRESH_TOKEN",
            "arg": None,
            "default": None,
        },
        # WORKBENCH WORKFLOW SERVICE
        {
            "attr": "workbench_workflow_service_url",
            "env": "WORKBENCH_WORKFLOW_SERVICE_URL",
            "arg": None,
            "default": DEFAULT_WORKBENCH_WORKFLOW_SERVICE_URL,
        },
        {
            "attr": "workbench_workflow_service_refresh_token",
            "env": "WORKBENCH_WORKFLOW_SERVICE_REFRESH_TOKEN",
            "arg": None,
            "default": None,
        },
        {"attr": "all", "env": None, "arg": "all", "default": False},
    ]

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

    @classmethod
    def __new__(cls, cli_kwargs):
        config = super(ConfigEnv, cls).__new__(cls)

        cls._cli_kwargs = cli_kwargs

        for cp in cls._configuration_parameters:
            config.__setattr__(
                cp["attr"], cls.__eval(cp["env"], cp["arg"], cp["default"])
            )

        return config
