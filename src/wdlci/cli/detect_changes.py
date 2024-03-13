import jsonpickle
import sys
import WDL
from wdlci.constants import CHANGES_JSON
from wdlci.model.changeset import Changeset
from wdlci.config import Config
from wdlci.config.config_file import WorkflowTaskConfig, WorkflowTaskTestConfig
from wdlci.exception.wdl_test_cli_exit_exception import WdlTestCliExitException


def detect_changes_handler(kwargs):
    try:
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
                    if (
                        previous_digest != task_digest
                        and workflow_config.tasks[task_name].tests
                    ):
                        print(f"Task change detected [{workflow} - {task_name}]")
                        workflow_change = changeset.add_workflow_change(workflow)
                        workflow_change.add_task_change(task_name)
                else:
                    print(f"New task detected [{workflow} - {task_name}]")
                    workflow_change = changeset.add_workflow_change(workflow)
                    workflow_change.add_task_change(task_name)

        if len(changeset.workflow_changes) == 0:
            print("No new or modified tasks detected")

        encoded = jsonpickle.encode(changeset)
        open(CHANGES_JSON, "w").write(encoded)
    except WdlTestCliExitException as e:
        print(f"exiting with code {e.exit_code}, message: {e.message}")
        sys.exit(e.exit_code)
