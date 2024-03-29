import json
from wdlci.constants import CONFIG_JSON
from wdlci.exception.wdl_test_cli_exit_exception import WdlTestCliExitException
import os.path


class ConfigFile(object):
    @classmethod
    def __new__(cls, initialize, *args, **kwargs):
        if initialize:
            workflows = {}
            engines = {}
            test_params = {"global_params": {}, "engine_params": {}}
        else:
            if os.path.exists(CONFIG_JSON):
                json_dict = json.load(open(CONFIG_JSON, "r"))
                workflows = {
                    key: WorkflowConfig.__new__(key, json_dict["workflows"][key])
                    for key in json_dict["workflows"].keys()
                }
                engines = {
                    key: EngineConfig.__new__(key, json_dict["engines"][key])
                    for key in json_dict["engines"].keys()
                }
                test_params = TestParams.__new__(json_dict["test_params"])
            else:
                raise WdlTestCliExitException(
                    f"Config file [{CONFIG_JSON}] not found; try running `wdl-cli generate-config` to initialize a config file",
                    1,
                )

        instance = super(ConfigFile, cls).__new__(cls)
        instance.__init__(workflows, engines, test_params)
        return instance

    def __init__(self, workflows, engines, test_params):
        self.workflows = workflows
        self.engines = engines
        self.test_params = test_params

    def get_task(self, workflow_key, task_key):
        if task_key in self.workflows[workflow_key].tasks:
            return self.workflows[workflow_key].tasks[task_key]
        else:
            return None


class WorkflowConfig(object):
    @classmethod
    def __new__(cls, workflow_key, json_dict):
        name = json_dict["name"]
        description = json_dict["description"]
        tasks = {
            key: WorkflowTaskConfig.__new__(key, json_dict["tasks"][key])
            for key in json_dict["tasks"].keys()
        }

        instance = super(WorkflowConfig, cls).__new__(cls)
        instance.__init__(workflow_key, name, description, tasks)
        return instance

    def __init__(self, key, name, description, tasks):
        self.key = key
        self.name = name
        self.description = description
        self.tasks = tasks


class WorkflowTaskConfig(object):
    @classmethod
    def __new__(cls, task_key, json_dict):
        digest = json_dict["digest"]
        tests = [
            WorkflowTaskTestConfig.__new__(json_elem)
            for json_elem in json_dict["tests"]
        ]

        instance = super(WorkflowTaskConfig, cls).__new__(cls)
        instance.__init__(task_key, digest, tests)
        return instance

    def __init__(self, key, digest, tests):
        self.key = key
        self.digest = digest
        self.tests = tests


class WorkflowTaskTestConfig(object):
    @classmethod
    def __new__(cls, json_dict):
        instance = super(WorkflowTaskTestConfig, cls).__new__(cls)
        instance.__init__(json_dict["inputs"], json_dict["output_tests"])
        return instance

    def __init__(self, inputs, output_tests):
        self.inputs = inputs
        self.output_tests = output_tests


class EngineConfig(object):
    @classmethod
    def __new__(cls, key, json_dict):
        instance = super(EngineConfig, cls).__new__(cls)
        engine_name = json_dict.get("name", "")
        instance.__init__(key, json_dict["enabled"], engine_name)
        return instance

    def __init__(self, key, enabled, name):
        self.key = key
        self.enabled = enabled
        self.name = name


class TestParams(object):
    @classmethod
    def __new__(cls, json_dict):
        instance = super(TestParams, cls).__new__(cls)
        instance.__init__(json_dict["global_params"], json_dict["engine_params"])
        return instance

    def __init__(self, global_params, engine_params):
        self.global_params = global_params
        self.engine_params = engine_params
