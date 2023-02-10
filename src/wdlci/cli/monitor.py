import jsonpickle
import os
import sys
import time
from wdlci.auth.refresh_token_auth import RefreshTokenAuth
from wdlci.constants import *
from wdlci.config import Config
from wdlci.exception.wdl_test_cli_exit_exception import WdlTestCliExitException
from wdlci.workbench.ewes_client import EwesClient
from wdlci.model.submission_state import SubmissionStateWorkflowRun


def validate_input(config):
    required_attrs = [
        "wallet_url",
        "wallet_client_id",
        "wallet_client_secret",
        "workbench_namespace",
        "workbench_ewes_url",
        "workbench_ewes_refresh_token",
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


def monitor_handler(kwargs):
    try:
        # load and validate config
        Config.load(kwargs)
        config = Config.instance()
        validate_input(config)

        # load access tokens, clients
        ewes_auth = RefreshTokenAuth(
            config.env.workbench_ewes_refresh_token, ["wes", "engine"]
        )
        ewes_client = EwesClient(ewes_auth)

        # load submission state
        submission_state = jsonpickle.decode(open(SUBMISSION_JSON, "r").read())

        # monitor all runs until finished (success or fail)
        # once all runs are finished, proceed to next step
        all_workflow_runs_complete = False
        to_sleep = False
        while not all_workflow_runs_complete:
            if to_sleep:
                time.sleep(60)
            to_sleep = True

            for workflow_run in submission_state.workflow_runs:
                # inspect workflow run status, update if finished
                if not workflow_run.is_done():
                    ewes_client.poll_workflow_run_status_and_update(workflow_run)

                # perform output validation step for runs that completed successfully
                if (
                    workflow_run.status
                    == SubmissionStateWorkflowRun.STATUS_FINISH_SUCCESS
                    and workflow_run.validation_status
                    == SubmissionStateWorkflowRun.VALIDATION_UNSTARTED
                ):
                    # TODO add output validation logic
                    pass

            # iterate through all runs, if all runs are in a terminal state,
            # move onto the next step
            runs_done = True
            for workflow_run in submission_state.workflow_runs:
                if not workflow_run.is_done():
                    runs_done = False
            if runs_done:
                all_workflow_runs_complete = True

        # assess completion and validation status of each run
        # exit successfully only if all runs:
        #   - completed successfully
        #   - have outputs that match the expected
        fail_n = 0
        for workflow_run in submission_state.workflow_runs:
            if (
                workflow_run.status == SubmissionStateWorkflowRun.STATUS_FINISH_SUCCESS
                and workflow_run.validation_status
                == SubmissionStateWorkflowRun.VALIDATION_SUCCESS
            ):
                # success condition
                pass
            elif workflow_run.status == SubmissionStateWorkflowRun.STATUS_FINISH_FAIL:
                fail_n += 1
                print(
                    f"run with id '{workflow_run.wes_run_id}' failed execution with a state of {workflow_run.wes_state}"
                )
            elif (
                workflow_run.status == SubmissionStateWorkflowRun.STATUS_FINISH_SUCCESS
                and workflow_run.validation_status
                == SubmissionStateWorkflowRun.VALIDATION_FAIL
            ):
                fail_n += 1
                print(
                    f"run with id '{workflow_run.wes_run_id}' failed output validation. message: {workflow_run.validation_message}"
                )
            else:
                fail_n += 1
                print(
                    f"run with id '{workflow_run.wes_run_id}' failed with an unspecified error"
                )

        submission_state_encoded = jsonpickle.encode(submission_state)
        open(SUBMISSION_JSON, "w").write(submission_state_encoded)

        if fail_n > 0:
            raise WdlTestCliExitException(
                f"{fail_n} workflow run(s) failed at the execution and/or validation stage",
                1,
            )

        # TODO add successful finish message
        print(
            "Monitoring and validation complete. All workflow runs completed successfully and output the expected results"
        )

    except WdlTestCliExitException as e:
        print(f"exiting with code {e.exit_code}, message: {e.message}")
        sys.exit(e.exit_code)
