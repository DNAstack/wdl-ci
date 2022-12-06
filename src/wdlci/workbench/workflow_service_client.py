import requests
from wdlci.config import Config

class WorkflowServiceClient(object):
    
    def __init__(self, workflow_service_auth):
        self.workflow_service_auth = workflow_service_auth
    
    def register_workflow(self, filename):
        payload = {
            "name": "WDL CI Test Workflow",
            "description": "test workflow",
            "files": [
                {
                    "path": "TODO",
                    "file_type": "PRIMARY_DESCRIPTOR",
                    "content": ""
                }
            ]
        }

    def deregister_namespace_workflows(self):
        pass
    
    def __get_url(self):
        return Config.instance().workbench_workflow_service_url
