from wdlci.config import Config
import WDL
from wdlci.config.config_file import WorkflowConfig, WorkflowTaskConfig
from wdlci.constants import CONFIG_JSON
import os.path


def update_task_digests_handler(kwargs):
    Config.load(kwargs)
    config = Config.instance()

    config_updated = False

    # Update or initialize workflows and tasks
    cwd = os.getcwd()
    wdl_files = []
    for root_path, subfolders, filenames in os.walk(cwd):
        for filename in filenames:
            if filename.endswith(".wdl"):
                wdl_files.append(
                    os.path.relpath(os.path.join(root_path, filename), cwd)
                )

    for workflow_path in wdl_files:
        if workflow_path not in config.file.workflows:
            config.file.workflows[workflow_path] = WorkflowConfig.__new__(
                workflow_path, {"name": "", "description": "", "tasks": {}}
            )
            print(f"Adding workflow [{workflow_path}]")
            config_updated = True

        doc = WDL.load(workflow_path)

        for task in doc.tasks:
            task_name = task.name
            task_digest = task.digest

            if task_name in config.file.workflows[workflow_path].tasks:
                if (
                    config.file.workflows[workflow_path].tasks[task_name].digest
                    != task_digest
                ):
                    print(f"Updating task [{workflow_path} - {task_name}]")
                    config.file.workflows[workflow_path].tasks[
                        task_name
                    ].digest = task_digest
                    config_updated = True
            else:
                print(f"Adding task [{workflow_path} - {task_name}]")
                task_config = WorkflowTaskConfig.__new__(
                    task_name, {"digest": task_digest, "tests": []}
                )
                config.file.workflows[workflow_path].tasks[task_name] = task_config
                config_updated = True

    if config_updated:
        config.write()
        print(f"Wrote config to [{CONFIG_JSON}]")
    else:
        print("No workflow or task changes detected")
