import WDL
import os
import sys
import re

from wdlci.config import Config
from wdlci.config.config_file import WorkflowTaskConfig, WorkflowTaskTestConfig
from wdlci.exception.wdl_test_cli_exit_exception import WdlTestCliExitException

output_file_name_pattern = re.compile(r"\b\w+\?*\s+(\S+|\S+\[\S+\])\s+=")


def coverage_handler(kwargs):
    try:
        """ """
        # Load the config file
        Config.load(kwargs)
        # Get the config instance
        config = Config.instance()
        output_tests = {}
        # Iterate over each workflow in the config file
        for workflow_name, workflow_config in config.file.workflows.items():
            # Iterate over each task in the workflow
            for task_name, task_config in workflow_config.tasks.items():
                # Iterate over each test in the task
                for test_config in task_config.tests:
                    # Iterate over each output in the test
                    for output, test in test_config.output_tests.items():
                        # Add the output to the dictionary if it is not already present
                        if output not in output_tests:
                            output_tests[output] = []
                        output_tests[output].append(test["test_tasks"])

        # Load all WDL files in the directory
        cwd = os.getcwd()
        wdl_files = []
        for root_path, subfolders, filenames in os.walk(cwd):
            for filename in filenames:
                if filename.endswith(
                    ".wdl"
                ):  # Need to make sure this does NOT look in custom_tests dir
                    wdl_files.append(
                        os.path.relpath(os.path.join(root_path, filename), cwd)
                    )

        # Initialize counters
        all_outputs = all_tests = workflow_outputs = workflow_tests = 0

        # Iterate over each WDL file
        for wdl_file in wdl_files:
            # Strip everything except workflow name
            wdl_filename = wdl_file.split("/")[-1]
            # Load the WDL document
            doc = WDL.load(wdl_file)

            # Calculate and print the workflow coverage
            for task in doc.tasks:
                task_outputs = len(task.outputs)
                workflow_outputs += task_outputs
                for output in task.outputs:
                    if output.name in output_tests.keys():
                        workflow_tests += 1
            if not workflow_outputs:
                print(
                    f"\nworkflow: {wdl_filename} has no outputs and thus cannot have any associated tests"
                )
            if workflow_tests and workflow_outputs:
                workflow_coverage = (workflow_tests / workflow_outputs) * 100
                print(f"\nworkflow: {wdl_filename}: {workflow_coverage:.2f}%")
            elif workflow_outputs and not workflow_tests:
                print(
                    f"[WARN]: workflow: {wdl_filename} has outputs but no associated tests\n"
                )

            # Iterate over each task in the WDL document
            for task in doc.tasks:
                task_outputs = []
                tested_outputs = []
                # Create a list of outputs that are present in the task/worfklow but not in the config JSON using the output_tests dictionary
                missing_config_outputs = [
                    output_file_name_pattern.search(str(output)).group(1)
                    for output in task.outputs
                    if output.name not in output_tests
                ]

                # Count the number of outputs for the task
                task_outputs = task.outputs
                # total_outputs += task_outputs
                all_outputs += len(task_outputs)

                # Check if there are tests for each output
                for output in task.outputs:
                    if output.name in output_tests.keys():
                        tested_outputs.append(output.name)
                        all_tests += 1
                # Check if task_outputs is non-zero
                if task_outputs:
                    # Calculate and print the task coverage
                    task_coverage = (len(tested_outputs) / len(task_outputs)) * 100
                    print(f"\ttask.{task.name}: {task_coverage:.2f}%")
                if missing_config_outputs:
                    print(
                        f"\t[WARN]: Missing tests in wdl-ci.config.json for {missing_config_outputs} in task {task.name}"
                    )

        # Calculate and print the total coverage
        if all_outputs:
            total_coverage = (all_tests / all_outputs) * 100
            print(f"\nTotal coverage: {total_coverage:.2f}%")

    except WdlTestCliExitException as e:
        print(f"exiting with code {e.exit_code}, message: {e.message}")
        sys.exit(e.exit_code)
