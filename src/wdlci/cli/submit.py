import jsonpickle
import os
import sys
import itertools
import WDL
from importlib.resources import files
from wdlci.auth.refresh_token_auth import RefreshTokenAuth
from wdlci.config import Config
from wdlci.config.config_file import WorkflowConfig
from wdlci.constants import *
from wdlci.exception.wdl_test_cli_exit_exception import WdlTestCliExitException
from wdlci.model.changeset import Changeset
from wdlci.model.submission_state import SubmissionState, SubmissionStateWorkflowRun
from wdlci.workbench.ewes_client import EwesClient
from wdlci.workbench.workflow_service_client import WorkflowServiceClient
from wdlci.utils.hydrate_params import HydrateParams
from wdlci.utils.validate_inputs import validate_inputs
from wdlci.utils.write_workflow import write_workflow


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

    if not config.env.all:
        if not os.path.exists(CHANGES_JSON):
            raise WdlTestCliExitException(
                f"cannot determine changed tasks, {CHANGES_JSON} not found", 1
            )


def submit_handler(kwargs):
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

        workflow_service_auth = RefreshTokenAuth(
            config.env.workbench_workflow_service_refresh_token, ["workflows"]
        )
        workflow_service_client = WorkflowServiceClient(workflow_service_auth)

        # load test and changeset info
        # identify tests that need to be run and add to submission set
        changeset = Changeset.from_json(CHANGES_JSON)
        submission_state = SubmissionState()

        # register workflow(s)
        tasks_to_test = dict()
        for workflow_key in changeset.get_workflow_keys():
            for task_key in changeset.get_tasks(workflow_key):
                doc = WDL.load(workflow_key)
                doc_tasks = {task.name: task for task in doc.tasks}
                task = config.file.get_task(workflow_key, task_key)

                # Register and create workflows for all tasks with tests
                for test_index, test_input_set in enumerate(task.tests):
                    doc_main_task = doc_tasks[task_key]

                    # TODO Rejig output format pending update of wdl-ci.config.json file format
                    #   trying to get {output_name: {"value": output_value, "test_tasks": ["test", "task", "names"]}}
                    #   won't be necessary once wdl-ci config file format has been updated
                    test_outputs = test_input_set.outputs
                    test_outputs_restructured = {}
                    for test_output_name, test_output_value in test_outputs.items():
                        test_outputs_restructured[test_output_name] = {
                            "value": test_output_value,
                            "test_tasks": test_input_set.test_tasks,
                        }

                    workflow_name = f"wdlci_{doc_main_task.name}_{test_index}"
                    # TODO update with set of test_tasks gathered across all outputs/tests rather than '-'.join(test_input_set.test_tasks) once config file format updated
                    test_key = f"{workflow_key}-{task_key}-{test_index}-{'-'.join(test_input_set.test_tasks)}"

                    workflow_config = WorkflowConfig.__new__(
                        test_key,
                        {
                            "name": test_key,
                            "description": f"Workflow: {workflow_key}\nTask: {task_key}\nTest set index: {test_index}",
                            "tasks": {},
                        },
                    )

                    # TODO pass test_outputs, not test_outputs_restructured, once config file structure has been updated
                    write_workflow(
                        workflow_name,
                        doc_main_task,
                        test_outputs_restructured,
                        test_key,
                    )

                    # TODO validate the workflow; ignore warnings, only check errors

                    workflow_id = workflow_service_client.register_workflow(
                        test_key,
                        workflow_config,
                        transient=True,
                    )
                    submission_state.add_workflow(test_key, workflow_id)

                    tasks_to_test[test_key] = {
                        "task": task,
                        "doc_task": doc_main_task,
                        "test_case": task.tests[test_index],
                        "workflow_name": workflow_name,
                        "test_index": test_index,
                    }

        for engine_id in config.file.engines.keys():
            if config.file.engines[engine_id].enabled:
                # get engines by id and add to state
                engine_json = ewes_client.get_engine(engine_id)
                submission_state.add_engine(engine_id, engine_json)

                for test_key, task_config in tasks_to_test.items():
                    print(f"Setting up workflow run for test {test_key}")
                    test_case = task_config["test_case"]

                    task_inputs = validate_inputs(
                        test_key, task_config["doc_task"], test_case.inputs
                    )

                    source_params = {
                        **config.file.test_params.global_params,
                        **config.file.test_params.engine_params[engine_id],
                    }
                    inputs_hydrated = HydrateParams.hydrate(
                        source_params, task_inputs, task_config["workflow_name"]
                    )
                    outputs_hydrated = HydrateParams.hydrate(
                        source_params, test_case.outputs, task_config["workflow_name"]
                    )

                    for output_key, output_value in outputs_hydrated.items():
                        output_key_split = output_key.split(".")
                        test_output_key = (
                            output_key_split[0] + ".TEST_OUTPUT_" + output_key_split[1]
                        )
                        inputs_hydrated[f"{test_output_key}"] = output_value

                    workflow_id = submission_state.workflows[test_key]._workflow_id

                    workflow_run = submission_state.add_workflow_run(
                        test_key,
                        workflow_id,
                        task_config["task"],
                        task_config["test_index"],
                        engine_id,
                        inputs_hydrated,
                        outputs_hydrated,
                    )
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
            raise WdlTestCliExitException(
                f"{n_submit_failures} workflow run(s) failed to submit to WES", 1
            )

        print("Submission process complete. All workflow runs submitted successfully")

    except WdlTestCliExitException as e:
        print(f"exiting with code {e.exit_code}, message: {e.message}")
        sys.exit(e.exit_code)
