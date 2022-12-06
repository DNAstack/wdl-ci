import jsonpickle
import os
import sys
from wdltest.auth.refresh_token_auth import RefreshTokenAuth
from wdltest.config import Config
from wdltest.constants import *
from wdltest.exception.wdl_test_cli_exit_exception import WdlTestCliExitException
from wdltest.model.changeset import Changeset
from wdltest.model.testset import TestSet
from wdltest.model.submission_set import SubmissionSet, Submission
from wdltest.workbench.ewes_client import EwesClient
from wdltest.workbench.workflow_service_client import WorkflowServiceClient

def validate_input(config):
    required_attrs = [
        "wallet_url",
        "wallet_client_id",
        "wallet_client_secret",
        "workbench_ewes_url",
        "workbench_ewes_refresh_token",
        "workbench_workflow_service_url",
        "workbench_workflow_service_refresh_token"
    ]
    for req_attr in required_attrs:
        if not getattr(config, req_attr):
            raise WdlTestCliExitException(f"required attribute: {req_attr} is not set", 1)

    if not config.all:
        if not os.path.exists(CHANGES_JSON):
            raise WdlTestCliExitException(f"cannot determine changed tasks, {CHANGES_JSON} not found", 1)

def submit_handler(kwargs):
    try:
        # load and validate config
        Config.load(kwargs)
        config = Config.instance()
        validate_input(config)

        # load access tokens, register workflow and engine
        ewes_auth = RefreshTokenAuth(config.workbench_ewes_refresh_token, ["wes", "engine"])
        ewes_client = EwesClient(ewes_auth)
        ewes_client.register_engine()

        workflow_service_auth = RefreshTokenAuth(config.workbench_workflow_service_refresh_token, ["workflows"])
        workflow_service_client = WorkflowServiceClient(workflow_service_auth)
        workflow_service_client.register_workflow()

        # load test and changeset info
        # identify tests that need to be run and add to submission set
        testset = TestSet.from_json(TESTS_JSON)
        changeset = Changeset.from_json(CHANGES_JSON)
        submission_set = SubmissionSet()
        
        for workflow_key in changeset.get_workflow_keys():
            for task in changeset.get_tasks(workflow_key):
                for test_case in testset.get_task_tests(workflow_key, task):
                    submission_set.add_submission(workflow_key, task, test_case)
        
        # submit all WDL jobs
        submission_set.submit_all()

        # validate all jobs were successfully submitted
        for submission in submission_set.submissions:
            if submission.status != Submission.STATUS_SUBMITTED:
                raise WdlTestCliExitException(f"test case was not submitted successfully. workflow: {submission.workflow}, task: {submission.task}.", 1)
        
        submission_set_encoded = jsonpickle.encode(submission_set)
        open(SUBMISSION_JSON, "w").write(submission_set_encoded)

    except WdlTestCliExitException as e:
        print(f"exiting with code {e.exit_code}, message: {e.message}")
        sys.exit(e.exit_code)
