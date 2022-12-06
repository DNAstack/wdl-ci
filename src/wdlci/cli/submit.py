import jsonpickle
import os
import sys
from wdlci.auth.refresh_token_auth import RefreshTokenAuth
from wdlci.config import Config
from wdlci.constants import *
from wdlci.exception.wdl_test_cli_exit_exception import WdlTestCliExitException
from wdlci.model.changeset import Changeset
from wdlci.model.submission_state import SubmissionState
from wdlci.workbench.ewes_client import EwesClient
from wdlci.workbench.workflow_service_client import WorkflowServiceClient

def validate_input(config):
    required_attrs = [
        "wallet_url",
        "wallet_client_id",
        "wallet_client_secret",
        "workbench_namespace",
        "workbench_ewes_url",
        "workbench_ewes_refresh_token",
        "workbench_workflow_service_url",
        "workbench_workflow_service_refresh_token"
    ]
    for req_attr in required_attrs:
        if not getattr(config.env, req_attr):
            raise WdlTestCliExitException(f"required attribute: {req_attr} is not set", 1)

    if not config.env.all:
        if not os.path.exists(CHANGES_JSON):
            raise WdlTestCliExitException(f"cannot determine changed tasks, {CHANGES_JSON} not found", 1)

def submit_handler(kwargs):
    try:
        # load and validate config
        Config.load(kwargs)
        config = Config.instance()
        validate_input(config)

        # load access tokens, clients
        ewes_auth = RefreshTokenAuth(config.env.workbench_ewes_refresh_token, ["wes", "engine"])
        ewes_client = EwesClient(ewes_auth)

        workflow_service_auth = RefreshTokenAuth(config.env.workbench_workflow_service_refresh_token, ["workflows"])
        workflow_service_client = WorkflowServiceClient(workflow_service_auth)

        # load test and changeset info
        # identify tests that need to be run and add to submission set
        changeset = Changeset.from_json(CHANGES_JSON)
        submission_state = SubmissionState()

        # register workflow(s)
        print("register this...")
        for workflow_key in changeset.get_workflow_keys():
            print(workflow_key)
            workflow_service_client.register_workflow(workflow_key, config.file.workflows[workflow_key])

        # for engine_key in config.file.engines.keys():
        #     if config.file.engines[engine_key].enabled:
        #         for workflow_key in changeset.get_workflow_keys():
        #             for task in changeset.get_tasks(workflow_key):
        #                 for test_i in range(0, len(config.file.workflows[workflow_key].tasks[task].tests)):
        #                     test_case = config.file.workflows[workflow_key].tasks[task].tests[test_i]
        #                     print(test_case)
        #                     # submission_set.add_submission(workflow_key, task, test_case)
        # 
        # workflow_service_client.register_workflow()
        # 
        # # submit all WDL jobs
        # submission_set.submit_all()
# 
        # # validate all jobs were successfully submitted
        # for submission in submission_set.submissions:
        #     if submission.status != Submission.STATUS_SUBMITTED:
        #         raise WdlTestCliExitException(f"test case was not submitted successfully. workflow: {submission.workflow}, task: {submission.task}.", 1)
        # 
        # # submission_set_encoded = jsonpickle.encode(submission_set)
        # # open(SUBMISSION_JSON, "w").write(submission_set_encoded)

    except WdlTestCliExitException as e:
        print(f"exiting with code {e.exit_code}, message: {e.message}")
        sys.exit(e.exit_code)
