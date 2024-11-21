import WDL
import os
import sys
import re

from wdlci.config import Config
from wdlci.exception.wdl_test_cli_exit_exception import WdlTestCliExitException

output_file_name_pattern = re.compile(r"(\b\w+\b)\s*=")


def coverage_handler(kwargs):
    try:
        # Load the config file
        Config.load(kwargs)
        # Get the config instance
        config = Config.instance()
        output_tests = {}
        # Iterate over each workflow in the config file
        for _, workflow_config in config.file.workflows.items():
            # Iterate over each task in the workflow
            for _, task_config in workflow_config.tasks.items():
                # Iterate over each test in the task
                for test_config in task_config.tests:
                    # Iterate over each output in the test
                    for output, test in test_config.output_tests.items():
                        # Add the output to the dictionary if it is not already present
                        if output not in output_tests:
                            output_tests[output] = []
                        # Check if 'test_tasks' key exists in the test dictionary and is not empty and append to output_tests if present and not empty
                        if "test_tasks" in test and test["test_tasks"]:
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

        # Initialize counters/lists
        all_outputs = 0
        all_tests = []
        untested_tasks = {}
        untested_optional_outputs = []
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
                missing_outputs = [
                    output_file_name_pattern.search(str(output)).group(1)
                    for output in task.outputs
                    if output.name not in output_tests_keys
                    or (
                        output.name in output_tests_keys
                        and not output_tests[output.name]
                    )
                ]

                # Count the number of outputs for the task
                all_outputs += len(task.outputs)
                workflow_outputs += len(task.outputs)

                # Check if there are tests for each output
                for output in task.outputs:
                    if (
                        output.name in output_tests_keys
                        and output_tests[output.name] != []
                    ):
                        task_tests.append(output.name)
                        workflow_tests.append(output.name)
                        all_tests.append(output.name)
                    if (
                        output.type.optional
                        and output.name not in output_tests_keys
                        or (
                            output.name in output_tests_keys
                            and output_tests[output.name] == []
                        )
                    ):
                        untested_optional_outputs.append(output.name)
                # Print task coverage for tasks with outputs and tests
                if task.outputs and task_tests:
                    # Calculate and print the task coverage
                    task_coverage = (len(task_tests) / len(task.outputs)) * 100
                    print(f"task.{task.name}: {task_coverage:.2f}%")
                # If there are outputs but no tests for the entire task, add the task to the untested_tasks list
                elif task.outputs and not task_tests:
                    if wdl_filename not in untested_tasks:
                        untested_tasks[wdl_filename] = []
                    untested_tasks[wdl_filename].append(task.name)
                if missing_outputs and task_tests:
                    print(
                        f"\t[WARN]: Missing tests in wdl-ci.config.json for {missing_outputs} in task {task.name}"
                    )
            # Print workflow coverage for tasks with outputs and tests
            if workflow_tests and workflow_outputs:
                workflow_coverage = (len(workflow_tests) / workflow_outputs) * 100
                print("-" * 150)
                print(f"workflow: {wdl_filename}: {workflow_coverage:.2f}%\n")
                ## TODO: Implement cutoff check for workflow coverage (e..g, adding sub-command/arg/flag for threshold; output any workflows with <80% coverage (and maybe even block merge if below a certain threshold), --workflow_name and just show me this one for example)
        # Warn the user about tasks that have no associated tests

        print("-" * 150)
        for workflow, tasks in untested_tasks.items():
            print(f"For {workflow}, these tasks are untested:")
            for task in tasks:
                print(f"\t{task}")
        # Warn the user about optional outputs that are not tested
        if untested_optional_outputs:
            print(
                f"\n[WARN]: These optional outputs are not tested: {untested_optional_outputs}"
            )
        else:
            print("\n✓ All optional outputs are tested")
        # Calculate and print the total coverage
        if all_tests and all_outputs:
            total_coverage = (len(all_tests) / all_outputs) * 100
            print(f"\nTotal coverage: {total_coverage:.2f}%")

    except WdlTestCliExitException as e:
        print(f"exiting with code {e.exit_code}, message: {e.message}")
        sys.exit(e.exit_code)
