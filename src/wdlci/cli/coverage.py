import WDL
import os
import sys
import re

from wdlci.config import Config
from wdlci.config.config_file import WorkflowTaskConfig, WorkflowTaskTestConfig
from wdlci.exception.wdl_test_cli_exit_exception import WdlTestCliExitException

output_file_name_pattern = re.compile(r"(\b\w+\b)\s*=")


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
                if filename.endswith(".wdl"):
                    wdl_files.append(
                        os.path.relpath(os.path.join(root_path, filename), cwd)
                    )

        # Initialize counters/lists for total coverage
        all_outputs = 0
        all_tests = []
        # Create a set of keys for the output_tests dictionary for faster lookup
        output_tests_keys = set(output_tests.keys())

        # Iterate over each WDL file
        for wdl_file in wdl_files:
            workflow_tests = []
            workflow_outputs = 0
            # Strip everything except workflow name
            wdl_filename = wdl_file.split("/")[-1]
            # Load the WDL document
            doc = WDL.load(wdl_file)

            # Iterate over each task in the WDL document
            for task in doc.tasks:
                task_tests = []
                # Create a list of outputs that are present in the task/worfklow but not in the config JSON using the output_tests dictionary
                missing_config_outputs = [
                    output_file_name_pattern.search(str(output)).group(1)
                    for output in task.outputs
                    if output.name not in output_tests
                ]

                # Count the number of outputs for the task
                all_outputs += len(task.outputs)
                workflow_outputs += len(task.outputs)

                # Check if there are tests for each output
                for output in task.outputs:
                    if output.name in output_tests_keys:
                        task_tests.append(output.name)
                        workflow_tests.append(output.name)
                        all_tests.append(output.name)
                # Check if task_outputs is non-zero
                if task.outputs:
                    # Calculate and print the task coverage
                    task_coverage = (len(task_tests) / len(task.outputs)) * 100
                    print(f"\ttask.{task.name}: {task_coverage:.2f}%")
                if missing_config_outputs:
                    print(
                        f"\t[WARN]: Missing tests in wdl-ci.config.json for {missing_config_outputs} in task {task.name}"
                    )
            if workflow_tests and workflow_outputs:
                workflow_coverage = (len(workflow_tests) / workflow_outputs) * 100
                print(f"workflow: {wdl_filename}: {workflow_coverage:.2f}%\n")

        # Calculate and print the total coverage
        if all_outputs:
            total_coverage = (len(all_tests) / all_outputs) * 100
            print(f"\nTotal coverage: {total_coverage:.2f}%")

    except WdlTestCliExitException as e:
        print(f"exiting with code {e.exit_code}, message: {e.message}")
        sys.exit(e.exit_code)