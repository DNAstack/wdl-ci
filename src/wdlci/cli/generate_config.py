from wdlci.config import Config
import WDL
from wdlci.config.config_file import WorkflowConfig, WorkflowTaskConfig
from wdlci.constants import CONFIG_JSON
from wdlci.utils.initialize_worklows_and_tasks import find_wdl_files
import os.path


def generate_config_handler(kwargs, update_task_digests=False):
    remove_deleted = kwargs["remove"]

    initialize = False if os.path.exists(CONFIG_JSON) else True
    if initialize:
        print("Generating config file")

    # if no config exists, we're definitely updating it
    config_updated = initialize

    Config.load(kwargs, initialize=initialize)
    config = Config.instance()

    # Initialize workflows and tasks
    wdl_files = find_wdl_files()

    for workflow_path in wdl_files:
        if workflow_path not in config.file.workflows:
            config.file.workflows[workflow_path] = WorkflowConfig.__new__(
                workflow_path, {"name": "", "description": "", "tasks": {}}
            )
            print(f"Adding workflow [{workflow_path}]")
            config_updated = True

        doc = WDL.load(workflow_path)

        # remove deleted tasks (whose workflows still exist)
        if remove_deleted:
            doc_tasks = [task.name for task in doc.tasks]
            tasks_to_remove = [
                task
                for task in config.file.workflows[workflow_path].tasks
                if task not in doc_tasks
            ]
            for task_name in tasks_to_remove:
                print(f"Removing task [{workflow_path} - {task_name}]")
                del config.file.workflows[workflow_path].tasks[task_name]
                config_updated = True

        for task in doc.tasks:
            task_name = task.name
            task_digest = task.digest if update_task_digests else ""

            # If the task is found in the config file and update_task_digests is set, update the task digest
            if task_name in config.file.workflows[workflow_path].tasks:
                if update_task_digests and (
                    config.file.workflows[workflow_path].tasks[task_name].digest
                    != task_digest
                ):
                    print(f"Updating task [{workflow_path} - {task_name}]")
                    config.file.workflows[workflow_path].tasks[
                        task_name
                    ].digest = task_digest
                    config_updated = True
            # If the task is not found, initialize it (to task.digest if update_task_digests, otherwise to "")
            else:
                print(f"Adding task [{workflow_path} - {task_name}]")
                task_config = WorkflowTaskConfig.__new__(
                    task_name, {"digest": task_digest, "tests": []}
                )
                config.file.workflows[workflow_path].tasks[task_name] = task_config
                config_updated = True

    # remove deleted workflows
    if remove_deleted:
        workflows_to_remove = [
            workflow_key
            for workflow_key in config.file.workflows
            if workflow_key not in wdl_files
        ]
        for workflow in workflows_to_remove:
            print(f"Removing workflow [{workflow}]")
            del config.file.workflows[workflow]
            config_updated = True

    if config_updated:
        config.write()
        print(f"Wrote config to [{CONFIG_JSON}]")
    else:
        print("No workflow or task changes detected")
