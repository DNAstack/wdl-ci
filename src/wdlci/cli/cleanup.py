import jsonpickle
import os
import sys
from wdlci.auth.refresh_token_auth import RefreshTokenAuth
from wdlci.config import Config
from wdlci.constants import *
from wdlci.exception.wdl_test_cli_exit_exception import WdlTestCliExitException
from wdlci.workbench.workflow_service_client import WorkflowServiceClient


def validate_input(config):
    required_attrs = [
        "wallet_url",
        "wallet_client_id",
        "wallet_client_secret",
        "workbench_namespace",
        "workbench_workflow_service_url",
        "workbench_workflow_service_refresh_token",
    ]
    for req_attr in required_attrs:
        if not getattr(config.env, req_attr):
            raise WdlTestCliExitException(
                f"required attribute: {req_attr} is not set", 1
            )

    if not os.path.exists(SUBMISSION_JSON):
        raise WdlTestCliExitException(f"submission state file not found", 1)


def cleanup_handler(kwargs):
    try:
        # load and validate config
        Config.load(kwargs)
        config = Config.instance()
        validate_input(config)

        # load access tokens, clients
        workflow_service_auth = RefreshTokenAuth(
            config.env.workbench_workflow_service_refresh_token,
            ["workflows", "namespace"],
        )
        workflow_service_client = WorkflowServiceClient(workflow_service_auth)

        submission_state = jsonpickle.decode(open(SUBMISSION_JSON, "r").read())
        for workflow in submission_state.workflows.values():
            workflow_service_client.delete_custom_workflow(workflow)

        print("Cleanup complete. Custom workflows purged from namespace")

    except WdlTestCliExitException as e:
        print(f"exiting with code {e.exit_code}, message: {e.message}")
        sys.exit(e.exit_code)
