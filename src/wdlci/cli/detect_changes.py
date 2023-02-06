import jsonpickle
import WDL
from wdlci.constants import CHANGES_JSON
from wdlci.model.changeset import Changeset
from wdlci.config import Config
from wdlci.config.config_file import WorkflowTaskConfig, WorkflowTaskTestConfig


def detect_changes_handler(kwargs):
    Config.load(kwargs)
    config = Config.instance()

    changeset = Changeset()

    for workflow, workflow_config in config.file.workflows.items():
        doc = WDL.load(workflow)

        for task in doc.tasks:
            task_name = task.name
            task_digest = task.digest

            if task_name in workflow_config.tasks:
                previous_digest = workflow_config.tasks[task_name].digest
                if previous_digest != task_digest:
                    print("Task change detected for " + workflow + ": " + task_name)
                    workflow_change = changeset.add_workflow_change(workflow)
                    workflow_change.add_task_change(task_name)

    encoded = jsonpickle.encode(changeset)
    open(CHANGES_JSON, "w").write(encoded)
