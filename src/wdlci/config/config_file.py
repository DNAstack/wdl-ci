import json
from wdlci.constants import CONFIG_JSON

class ConfigFile(object):

    @classmethod
    def __new__(cls, *args, **kwargs):
        json_dict = json.load(open(CONFIG_JSON, "r"))
        workflows = {key: WorkflowConfig.from_json(key, json_dict["workflows"][key]) for key in json_dict["workflows"].keys()}

        instance = super(ConfigFile, cls).__new__(cls)
        instance.__init__(workflows)

        return instance

    def __init__(self, workflows):
        self.workflows = workflows
        # self.engines = None
        # self.test_params = TestParams(json_dict["test_params"])

class WorkflowConfig(object):

    def __init__(self, key, name, description, tasks):
        self.key = key
        self.name = name
        self.description = description
        self.tasks = tasks
    
    @staticmethod
    def from_json(workflow_key, json_dict):
        tasks = {key: WorkflowTaskConfig.from_json(key, json_dict["tasks"][key]) for key in json_dict["tasks"].keys()}
        return WorkflowConfig(workflow_key, json_dict["name"], json_dict["description"], tasks)

class WorkflowTaskConfig(object):
    
    def __init__(self, key, digest, tests):
        self.key = key
        self.digest = digest
        self.tests = tests
    
    @staticmethod
    def from_json(task_key, json_dict):
        tests = [WorkflowTaskTestConfig.from_json(json_elem) for json_elem in json_dict["tests"]]
        return WorkflowTaskConfig(task_key, json_dict["digest"], tests)

class WorkflowTaskTestConfig(object):

    def __init__(self, inputs, outputs):
        self.inputs = inputs
        self.outputs = outputs
    
    @staticmethod
    def from_json(json_dict):
        return WorkflowTaskTestConfig(json_dict["inputs"], json_dict["outputs"])

class TestParams(object):

    def __init__(self, json_dict):
        self.global_params = json_dict["global"]
        self.engine_params = json_dict["engines"]
