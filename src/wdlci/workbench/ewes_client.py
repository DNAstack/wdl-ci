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
        headers = {
            "Authorization": "Bearer " + self.ewes_auth.access_token
        }

        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise WdlTestCliExitException(f"Could not get engine by specified id: '{engine_id}'")
        return response.json()

    def submit_workflow_run(self, workflow_run):
        env = Config.instance().env
        base_url, namespace = env.workbench_ewes_url, env.workbench_namespace
        url = f"{base_url}/{namespace}/ga4gh/wes/v1/runs"

        headers = {
            "Authorization": "Bearer " + self.ewes_auth.access_token
        }

        form_data = {
            "workflow_url": f"{env.workbench_workflow_service_url}/{env.workbench_namespace}/workflows/{workflow_run._workflow_id}/versions/latest/descriptor",
            "workflow_type": "WDL",
            "workflow_type_version": "1.0",
            "workflow_params": workflow_run._inputs,
            "workflow_engine_parameters": {
                "engine_id": workflow_run._engine_key
            }
        }

        response = requests.post(url, headers=headers, json=form_data)
        if response.status_code != 200:
            workflow_run.submit_fail()
        else:
            workflow_run.submit_success()
            wes_json = response.json()
            workflow_run.wes_run_id = wes_json["run_id"]
            workflow_run.wes_state = wes_json["state"]

    def poll_workflow_run_status_and_update(self, workflow_run):
        env = Config.instance().env
        base_url, namespace = env.workbench_ewes_url, env.workbench_namespace
        url = f"{base_url}/{namespace}/ga4gh/wes/v1/runs/{workflow_run.wes_run_id}/status"

        headers = {
            "Authorization": "Bearer " + self.ewes_auth.access_token
        }

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            wes_state = response.json()["state"]
            workflow_run.wes_state = wes_state

            if wes_state in set([
                "EXECUTOR_ERROR",
                "SYSTEM_ERROR",
                "CANCELED"
            ]):
                workflow_run.finish_fail()
            elif wes_state in set([
                "COMPLETE"
            ]):
                workflow_run.finish_success()

    def __get_url(self):
        return Config.instance().workbench_ewes_url