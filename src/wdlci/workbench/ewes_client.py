import json
import requests
from wdlci.config import Config
from wdlci.exception.wdl_test_cli_exit_exception import WdlTestCliExitException
from wdlci.model.submission_state import SubmissionStateWorkflowRun


class EwesClient(object):
    def __init__(self, ewes_auth):
        self.ewes_auth = ewes_auth

    def get_engine(self, engine_id):
        env = Config.instance().env
        base_url, namespace = env.workbench_ewes_url, env.workbench_namespace
        url = f"{base_url}/{namespace}/engines/{engine_id}"
        headers = {"Authorization": "Bearer " + self.ewes_auth.access_token}

        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise WdlTestCliExitException(
                f"Could not get engine by specified id: '{engine_id}'", 1
            )
        return response.json()

    def submit_workflow_run(self, workflow_run):
        env = Config.instance().env
        base_url, namespace = env.workbench_ewes_url, env.workbench_namespace
        url = f"{base_url}/{namespace}/ga4gh/wes/v1/runs"

        headers = {"Authorization": "Bearer " + self.ewes_auth.access_token}

        output_test_task_params = {
            k: workflow_run._outputs[k]["value"] for k in workflow_run._outputs.keys()
        }

        form_data = {
            "workflow_url": f"{env.workbench_workflow_service_url}/{env.workbench_namespace}/workflows/{workflow_run._workflow_id}/versions/v1_0_0/descriptor",
            "workflow_type": "WDL",
            "workflow_type_version": "1.0",
            "workflow_params": {**workflow_run._inputs, **output_test_task_params},
            "workflow_engine_parameters": {"engine_id": workflow_run._engine_key},
        }

        response = requests.post(url, headers=headers, json=form_data)
        if response.status_code != 200:
            workflow_run.submit_fail()
            print(f"Error [{response.status_code}] while submitting workflow")
        else:
            workflow_run.submit_success()
            wes_json = response.json()
            workflow_run.wes_run_id = wes_json["run_id"]
            workflow_run.wes_state = wes_json["state"]
            print(f"[{workflow_run._workflow_key}]: {wes_json['state']}")
            print("Workflow submission successful")

    def poll_workflow_run_status_and_update(self, workflow_run):
        env = Config.instance().env
        base_url, namespace = env.workbench_ewes_url, env.workbench_namespace
        url = (
            f"{base_url}/{namespace}/ga4gh/wes/v1/runs/{workflow_run.wes_run_id}/status"
        )

        headers = {"Authorization": "Bearer " + self.ewes_auth.access_token}

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            wes_state = response.json()["state"]
            print(f"[{workflow_run._workflow_key}]: {wes_state}")
            workflow_run.wes_state = wes_state

            if wes_state in set(["EXECUTOR_ERROR", "SYSTEM_ERROR", "CANCELED"]):
                workflow_run.finish_fail()
            elif wes_state in set(["COMPLETE"]):
                workflow_run.finish_success()

    def _print_stderr(self, stderr_url, headers, task_name):
        terminal_format_bold = "\033[1m"
        terminal_format_end = "\033[0m"
        print(
            f"{terminal_format_bold}═════ stderr ═════════════════════════════════════════ [{task_name}]{terminal_format_end}"
        )
        print()
        response = requests.get(stderr_url, headers=headers)
        print(response.content.decode("ascii"))
        print(
            f"{terminal_format_bold}═══════════════════════════════════════════════════════{terminal_format_end}"
        )
        print()

    def get_failed_task_logs(self, workflow_run):
        env = Config.instance().env
        base_url, namespace = env.workbench_ewes_url, env.workbench_namespace
        url = (
            f"{base_url}/{namespace}/ga4gh/wes/v1/runs/{workflow_run.wes_run_id}/tasks"
        )
        headers = {"Authorization": "Bearer " + self.ewes_auth.access_token}

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            for task in response.json()["tasks"]:
                if task["state"] == "EXECUTOR_ERROR":
                    task_name = task["pretty_name"].split(".")[1]
                    print(
                        f"EXECUTOR_ERROR for [{workflow_run._workflow_key} - {task_name}]."
                    )
                    self._print_stderr(task["stderr"], headers, task_name)

    def __get_url(self):
        return Config.instance().workbench_ewes_url
