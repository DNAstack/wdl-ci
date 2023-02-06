import jsonpickle


class Changeset(object):
    def __init__(self):
        self.workflow_changes = {}

    def add_workflow_change(self, path):
        if path in self.get_workflow_keys():
            workflow_change = self.workflow_changes[path]
        else:
            workflow_change = WorkflowChange()
            self.workflow_changes[path] = workflow_change
        return workflow_change

    def get_workflow_keys(self):
        return self.workflow_changes.keys()

    def get_tasks(self, workflow_key):
        return list(self.workflow_changes[workflow_key].task_changes)

    @staticmethod
    def from_json(json_file):
        return jsonpickle.decode(open(json_file, "r").read())


class WorkflowChange(object):
    def __init__(self):
        self.task_changes = set()

    def add_task_change(self, task):
        self.task_changes.add(task)
