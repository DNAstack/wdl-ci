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
        return self.workflows[workflow_key].tasks[task_key]


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

    def generate_task_workflow_config(self, workflow_key):
        """Generate a WorkflowConfig from a single task"""
        workflow_task_key = f"{workflow_key}-{self.key}"
        workflow_config = WorkflowConfig.__new__(
            workflow_task_key,
            {
                "name": f"{workflow_key} - {self.key}",
                "description": f"Stub workflow auto-generated from the '{self.key}' task, originating in the '{workflow_key}' workflow",
                "tasks": {},
            },
        )
        self.workflow_config = workflow_config

    def write_task_workflow_file(self, doc_task):
        """Materialize a workflow file with a call to this task"""
        outfile = self.workflow_config.key
        workflow_name = f"wdlci_{doc_task.name}"

        # Used during testing
        self.workflow_name = workflow_name
        self.task_inputs = doc_task.inputs

        with open(outfile, "w") as f:
            f.write(f"version {doc_task.effective_wdl_version}\n\n")

            # Write workflow
            f.write(f"workflow {workflow_name} {{\n")

            ## Inputs
            f.write("\tinput " + "{\n")
            for task_input in doc_task.inputs:
                f.write(f"\t\t{task_input}\n")
            f.write("\t}\n")
            f.write("\n")

            ## Calls
            f.write(f"\tcall {doc_task.name} {{\n")
            f.write("\t\tinput:\n")
            for index, task_input in enumerate(doc_task.inputs):
                trailing_comma = "" if index == len(doc_task.inputs) - 1 else ","
                input_name = task_input.name
                f.write(f"\t\t\t{input_name} = {input_name}{trailing_comma}\n")
            f.write("\t}\n")
            f.write("\n")

            ## Outputs
            f.write("\toutput {\n")
            for task_output in doc_task.outputs:
                f.write(
                    f"\t\t{task_output.type} {task_output.name} = {doc_task.name}.{task_output.name}\n"
                )
            f.write("\t}\n")
            f.write("\n")

            f.write("}\n")
            f.write("\n")

            # Write task
            f.write(f"task {doc_task.name} {{\n")

            ## Inputs
            f.write("\tinput " + "{\n")
            for task_input in doc_task.inputs:
                f.write(f"\t\t{task_input}\n")
            f.write("\t}\n")
            f.write("\n")

            ## Post inputs
            for post_input in doc_task.postinputs:
                f.write(f"\t{post_input}\n")
            f.write("\n")

            ## Command
            f.write("\tcommand <<<\n")
            f.write(f"\t\t{doc_task.command}\n")
            f.write("\t>>>\n")
            f.write("\n")

            ## Outputs
            f.write("\toutput {\n")
            for task_output in doc_task.outputs:
                f.write(f"\t\t{task_output}\n")
            f.write("\t}\n")
            f.write("\n")

            ## Runtime
            f.write("\truntime {\n")
            for runtime_key, runtime_value in doc_task.runtime.items():
                f.write(f"\t\t{runtime_key}: {runtime_value}\n")
            f.write("\t}\n")

            f.write("}\n")
            f.write("\n")


class WorkflowTaskTestConfig(object):
    @classmethod
    def __new__(cls, json_dict):
        instance = super(WorkflowTaskTestConfig, cls).__new__(cls)
        instance.__init__(json_dict["inputs"], json_dict["outputs"])
        return instance

    def __init__(self, inputs, outputs):
        self.inputs = inputs
        self.outputs = outputs


class EngineConfig(object):
    @classmethod
    def __new__(cls, key, json_dict):
        instance = super(EngineConfig, cls).__new__(cls)
        instance.__init__(key, json_dict["enabled"])
        return instance

    def __init__(self, key, enabled):
        self.key = key
        self.enabled = enabled


class TestParams(object):
    @classmethod
    def __new__(cls, json_dict):
        instance = super(TestParams, cls).__new__(cls)
        instance.__init__(json_dict["global_params"], json_dict["engine_params"])
        return instance

    def __init__(self, global_params, engine_params):
        self.global_params = global_params
        self.engine_params = engine_params
