import json
import os
import requests
from wdlci.config import Config
from wdlci.exception.wdl_test_cli_exit_exception import WdlTestCliExitException


class WorkflowServiceClient(object):
    def __init__(self, workflow_service_auth):
        self.workflow_service_auth = workflow_service_auth

    def register_workflow(self, workflow_key, workflow_config, transient=False):
        workflow_content = open(workflow_key, "r").read()
        payload = {
            "name": workflow_config.name,
            "description": workflow_config.description,
            "files": [
                {
                    "path": workflow_key,
                    "file_type": "PRIMARY_DESCRIPTOR",
                    "content": workflow_content,
                }
            ],
        }

        if transient:
            os.remove(workflow_key)

        env = Config.instance().env
        base_url, namespace = (
            env.workbench_workflow_service_url,
            env.workbench_namespace,
        )
        url = f"{base_url}/{namespace}/workflows"

        headers = {"Authorization": "Bearer " + self.workflow_service_auth.access_token}

        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            print(workflow_content)
            print(response.__dict__)
            raise WdlTestCliExitException(
                f"Could not register workflow [{workflow_key}] on Workbench", 1
            )

        return response.json()["id"]

    def purge_custom_workflows(self):
        env = Config.instance().env
        base_url, namespace = (
            env.workbench_workflow_service_url,
            env.workbench_namespace,
        )
        url = f"{base_url}/{namespace}"

        headers = {"Authorization": "Bearer " + self.workflow_service_auth.access_token}

        response = requests.delete(url, headers=headers)
        if response.status_code != 204:
            raise WdlTestCliExitException(
                "Error when purging custom workflows from namespace", 1
            )
