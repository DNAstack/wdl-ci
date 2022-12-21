import jsonpickle
import os
import sys
from wdlci.auth.refresh_token_auth import RefreshTokenAuth
from wdlci.config import Config
from wdlci.constants import *
from wdlci.exception.wdl_test_cli_exit_exception import WdlTestCliExitException
from wdlci.model.changeset import Changeset
from wdlci.model.submission_state import SubmissionState, SubmissionStateWorkflowRun
from wdlci.workbench.ewes_client import EwesClient
from wdlci.workbench.workflow_service_client import WorkflowServiceClient
from wdlci.utils.hydrate_params import HydrateParams

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
        for workflow_key in changeset.get_workflow_keys():
            workflow_id = workflow_service_client.register_workflow(workflow_key, config.file.workflows[workflow_key])
            submission_state.add_workflow(workflow_key, workflow_id)

        for engine_id in config.file.engines.keys():
            if config.file.engines[engine_id].enabled:
                # get engines by id and add to state
                engine_json = ewes_client.get_engine(engine_id)
                submission_state.add_engine(engine_id, engine_json)

                for workflow_key in changeset.get_workflow_keys():
                    for task in changeset.get_tasks(workflow_key):
                        for test_i in range(0, len(config.file.workflows[workflow_key].tasks[task].tests)):
                            test_case = config.file.workflows[workflow_key].tasks[task].tests[test_i]

                            source_params ={**config.file.test_params.global_params, **config.file.test_params.engine_params[engine_id]}
                            inputs_hydrated = HydrateParams.hydrate(source_params, test_case.inputs)
                            outputs_hydrated = HydrateParams.hydrate(source_params, test_case.outputs)

                            workflow_id = submission_state.workflows[workflow_key]._workflow_id

                            workflow_run = submission_state.add_workflow_run(workflow_key, workflow_id, task, test_i, engine_id, inputs_hydrated, outputs_hydrated)
                            ewes_client.submit_workflow_run(workflow_run)
        
        # write state to JSON for monitoring job
        submission_state_encoded = jsonpickle.encode(submission_state)
        open(SUBMISSION_JSON, "w").write(submission_state_encoded)

        # validate all jobs were successfully submitted
        n_submit_failures = 0
        for workflow_run in submission_state.workflow_runs:
            if workflow_run.status != SubmissionStateWorkflowRun.STATUS_SUBMIT_SUCCESS:
                # TODO add error log message
                n_submit_failures += 1
        
        if n_submit_failures > 0:
            raise WdlTestCliExitException(f"{n_submit_failures} workflow run(s) failed to submit to WES", 1)
        
        # TODO add successful finish message
        print("Submission process complete. All workflow runs submitted successfully")

    except WdlTestCliExitException as e:
        print(f"exiting with code {e.exit_code}, message: {e.message}")
        sys.exit(e.exit_code)
