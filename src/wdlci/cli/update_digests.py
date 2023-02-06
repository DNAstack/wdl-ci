from wdlci.config import Config
import WDL
from wdlci.config.config_file import WorkflowTaskConfig
from wdlci.constants import CONFIG_JSON


def update_digests_handler(kwargs):
    Config.load(kwargs)
    config = Config.instance()

    for workflow, workflow_config in config.file.workflows.items():
        doc = WDL.load(workflow)

        for task in doc.tasks:
            task_name = task.name
            task_digest = task.digest

            if task_name in workflow_config.tasks:
                if workflow_config.tasks[task_name].digest != task_digest:
                    print("Updated digest for task [{}/{}]".format(workflow, task_name))
                    config.file.workflows[workflow].tasks[
                        task_name
                    ].digest = task_digest
            else:
                print("Adding config for task [{}/{}]".format(workflow, task_name))
                task_config = WorkflowTaskConfig.__new__(
                    task_name, {"digest": task_digest, "tests": []}
                )
                config.file.workflows[workflow].tasks[task_name] = task_config

    config.write()
    print("Wrote updated config to [{}]".format(CONFIG_JSON))
