import json

class TestSet(object):
    
    def __init__(self, json_dict):
        self.workflows = {key: WorkflowTestSet.from_json(json_dict[key]) for key in json_dict.keys()}
    
    def get_task_digest(self, workflow, task):
        return self.workflows[workflow].tasks[task].digest
    
    def get_task_tests(self, workflow, task):
        return self.workflows[workflow].tasks[task].tests
    
    @staticmethod
    def from_json(json_file):
        return TestSet(json.load(open(json_file, "r")))

class WorkflowTestSet(object):

    def __init__(self, json_dict):
        self.tasks = {key: TaskTestSet.from_json(json_dict[key]) for key in json_dict.keys()}
    
    @staticmethod
    def from_json(json_dict):
        return WorkflowTestSet(json_dict)


class TaskTestSet(object):

    def __init__(self, digest, tests):
        self.digest = digest
        self.tests = tests
    
    @staticmethod
    def from_json(json_dict):
        return TaskTestSet(
            json_dict["digest"],
            [TaskTestCase.from_json(json_elem) for json_elem in json_dict["tests"]]
        )

class TaskTestCase(object):

    def __init__(self, inputs, outputs):
        self.inputs = inputs
        self.outputs = outputs
    
    @staticmethod
    def from_json(json_dict):
        return TaskTestCase(
            json_dict["inputs"],
            json_dict["outputs"]
        )
