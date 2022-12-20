import json
import requests
from wdlci.config import Config
from wdlci.exception.wdl_test_cli_exit_exception import WdlTestCliExitException

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
        # TODO remove debug print statements
        print(response.status_code)
        print(response.text)
        print(response.headers)

    def __get_url(self):
        return Config.instance().workbench_ewes_url