import jsonpickle
import os
import sys
import time
import re
import WDL
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
                    # Set validation status to VALIDATION_SUCCESS if the workflow succeeds
                    workflow_run.validation_status = (
                        SubmissionStateWorkflowRun.VALIDATION_SUCCESS
                    )
                # TODO set validation status to failed if the run finishes in the failed state

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
        task_status = dict()
        for workflow_run in submission_state.workflow_runs:
            # If a task fails during any of its runs, task_status[workflow_path][task]["succeeded"] will be updated to False
            # If all tests succeed for this task, it will be set to True
            task = workflow_run._task_key.key
            test_index = workflow_run._test_i
            workflow_path = re.sub(
                rf"-{task}-{test_index}$", "", workflow_run._workflow_key
            )
            if workflow_path in task_status:
                if task not in task_status[workflow_path]:
                    task_status[workflow_path][task] = {"succeeded": None}
            else:
                task_status[workflow_path] = {task: {"succeeded": None}}

            if (
                workflow_run.status == SubmissionStateWorkflowRun.STATUS_FINISH_SUCCESS
                and workflow_run.validation_status
                == SubmissionStateWorkflowRun.VALIDATION_SUCCESS
            ):
                if task_status[workflow_path][task]["succeeded"] != False:
                    task_status[workflow_path][task]["succeeded"] = True
            elif workflow_run.status == SubmissionStateWorkflowRun.STATUS_FINISH_FAIL:
                fail_n += 1
                print(
                    f"run with id '{workflow_run.wes_run_id}' failed execution with a state of {workflow_run.wes_state}"
                )
                task_status[workflow_path][task]["succeeded"] = False
            elif (
                workflow_run.status == SubmissionStateWorkflowRun.STATUS_FINISH_SUCCESS
                and workflow_run.validation_status
                == SubmissionStateWorkflowRun.VALIDATION_FAIL
            ):
                fail_n += 1
                print(
                    f"run with id '{workflow_run.wes_run_id}' failed output validation. message: {workflow_run.validation_message}"
                )
                task_status[workflow_path][task]["succeeded"] = False
            else:
                fail_n += 1
                print(
                    f"run with id '{workflow_run.wes_run_id}' failed with an unspecified error"
                )
                task_status[workflow_path][task]["succeeded"] = False

        submission_state_encoded = jsonpickle.encode(submission_state)
        open(SUBMISSION_JSON, "w").write(submission_state_encoded)

        # Update digests in config file for tasks that succeeded if --update-digests is set to true
        config_updated = False
        update_digests = kwargs["update_digests"]
        if update_digests:
            for workflow_path, tasks in task_status.items():
                doc = WDL.load(workflow_path)
                for task in doc.tasks:
                    task_name = task.name
                    if tasks.get(task_name):
                        if tasks[task_name]["succeeded"]:
                            print(
                                f"All tests succeeded for [{workflow_path} - {task_name}]. Updating task digest."
                            )
                            task_digest = task.digest
                            config.file.workflows[workflow_path].tasks[
                                task_name
                            ].digest = task_digest
                            config_updated = True
                        else:
                            print(
                                f"At least one test failed for [{workflow_path} - {task_name}]."
                            )

        if config_updated:
            config.write()
            print(f"Wrote updated config to [{CONFIG_JSON}]")

        if fail_n > 0:
            raise WdlTestCliExitException(
                f"{fail_n} workflow run(s) failed at the execution and/or validation stage",
                1,
            )

        print(
            "Monitoring and validation complete. All workflow runs completed successfully and output the expected results"
        )

    except WdlTestCliExitException as e:
        print(f"exiting with code {e.exit_code}, message: {e.message}")
        sys.exit(e.exit_code)
