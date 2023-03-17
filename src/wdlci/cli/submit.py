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

                    output_tests = test_input_set.output_tests

                    # Skip input sets with no test tasks defined for any output
                    all_test_tasks = [
                        test_task
                        for output in output_tests.values()
                        for test_task in output["test_tasks"]
                    ]
                    if len(all_test_tasks) == 0:
                        continue

                    workflow_name = f"wdlci_{doc_main_task.name}_{test_index}"
                    test_key = f"{workflow_key}-{task_key}-{test_index}"
                    struct_imports = test_input_set.struct_imports

                    workflow_config = WorkflowConfig.__new__(
                        test_key,
                        {
                            "name": test_key,
                            "description": f"Workflow: {workflow_key}\nTask: {task_key}\nTest set index: {test_index}",
                            "tasks": {},
                        },
                    )

                    try:
                        write_workflow(
                            workflow_name,
                            doc_main_task,
                            output_tests,
                            test_key,
                            struct_imports,
                        )
                    except WdlTestCliExitException as e:
                        print(f"exiting with code {e.exit_code}, message: {e.message}")
                        sys.exit(e.exit_code)

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
                        source_params,
                        task_inputs,
                        update_key=True,
                        workflow_name=task_config["workflow_name"],
                    )

                    output_tests_hydrated = {}
                    for (
                        output_test_key,
                        output_test_val,
                    ) in test_case.output_tests.items():
                        output_test_key_hydrated = f"{task_config['workflow_name']}.TEST_OUTPUT_{output_test_key}"
                        output_test_val_hydrated = HydrateParams.hydrate(
                            source_params, output_test_val, update_key=False
                        )
                        output_tests_hydrated[
                            output_test_key_hydrated
                        ] = output_test_val_hydrated

                    workflow_id = submission_state.workflows[test_key]._workflow_id

                    workflow_run = submission_state.add_workflow_run(
                        test_key,
                        workflow_id,
                        task_config["task"],
                        task_config["test_index"],
                        engine_id,
                        inputs_hydrated,
                        output_tests_hydrated,
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
