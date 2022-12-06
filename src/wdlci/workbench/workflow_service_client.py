import json
import requests
from wdlci.config import Config

class WorkflowServiceClient(object):
    
    def __init__(self, workflow_service_auth):
        self.workflow_service_auth = workflow_service_auth
    
    def register_workflow(self, workflow_key, workflow_config):
        payload = {
            "name": workflow_config.name,
            "description": workflow_config.description,
            "files": [
                {
                    "path": workflow_key,
                    "file_type": "PRIMARY_DESCRIPTOR",
                    "content": self.__escape_wdl(workflow_key)
                }
            ]
        }
        print(payload)

        env = Config.instance().env
        base_url, namespace = env.workbench_workflow_service_url, env.workbench_namespace
        url = f"{base_url}/{namespace}/workflows"

        headers = {
            "Authorization": "Bearer " + self.workflow_service_auth.access_token
        }
        
        response = requests.post(url, json=payload, headers=headers)
        print(response)
        print(response.status_code)
        print(response.text)

    def deregister_namespace_workflows(self):
        pass
    
    def __escape_wdl(self, filename):
        with open(filename, "r") as to_escape:
            file_data = to_escape.read()
            return json.dumps(file_data)
