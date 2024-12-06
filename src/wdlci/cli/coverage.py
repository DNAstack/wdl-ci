import WDL
import os
import sys
import re

from wdlci.config import Config
from wdlci.exception.wdl_test_cli_exit_exception import WdlTestCliExitException

output_file_name_pattern = re.compile(r"(\b\w+\b)\s*=")


def coverage_handler(kwargs):
    threshold = kwargs["target_coverage"]
    workflow_name_filter = kwargs["workflow_name"]
    print(f"Target coverage threshold: ", threshold)
    if workflow_name_filter:
        print(f"Workflow name filter: {workflow_name_filter}\n")
    else:
        print("Workflow name filter: None\n")
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
        for root_path, _, filenames in os.walk(cwd):
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
        # Flags to track if any tasks/workflows are below the threshold and if any workflows match the filter
        tasks_below_threshold = False
        workflows_below_threshold = False
        workflow_found = False

        # Iterate over each WDL file
        for wdl_file in wdl_files:
            workflow_tests = []
            workflow_outputs = 0
            # Strip everything except workflow name
            wdl_filename = wdl_file.split("/")[-1]
            # Load the WDL document
            doc = WDL.load(wdl_file)

            # If workflow_name_filter is provided, skip all other workflows
            if workflow_name_filter and workflow_name_filter not in wdl_filename:
                continue
            workflow_found = True

            # Iterate over each task in the WDL document
            for task in doc.tasks:
                task_tests = []
                # Create a list of outputs that are present in the task/worfklow but not in the config JSON using the output_tests dictionary
                missing_outputs = [
                    output_file_name_pattern.search(str(output)).group(1)
                    for output in task.outputs
                    if output.name not in output_tests.keys()
                    or (
                        output.name in output_tests.keys()
                        and not output_tests[output.name]
                    )
                ]

                # Count the number of outputs for the task
                all_outputs += len(task.outputs)
                workflow_outputs += len(task.outputs)

                # Check if there are tests for each output
                for output in task.outputs:
                    if output.name in output_tests.keys() and len(
                        output_tests[output.name] > 0
                    ):
                        task_tests.append(output.name)
                        workflow_tests.append(output.name)
                        all_tests.append(output.name)
                    elif (
                        output.type.optional
                        and output.name not in output_tests.keys()
                        or (
                            output.name in output_tests.keys()
                            and len(output_tests[output.name]) == 0
                        )
                    ):
                        untested_optional_outputs.append(output.name)
                # Print task coverage for tasks with outputs and tests
                if len(task.outputs) > 0 and len(task_tests) > 0:
                    # Calculate and print the task coverage
                    task_coverage = (len(task_tests) / len(task.outputs)) * 100
                    if threshold is None or task_coverage < threshold:
                        tasks_below_threshold = True
                        print(f"task.{task.name}: {task_coverage:.2f}%")
                # If there are outputs but no tests for the entire task, add the task to the untested_tasks list
                elif (
                    len(task.outputs) > 0 and not task_tests
                ):  # Consider building this into the above so that we can incorporate untested tasks into the threshold check/statement returned to user
                    if wdl_filename not in untested_tasks:
                        untested_tasks[wdl_filename] = []
                    untested_tasks[wdl_filename].append(task.name)
                if len(missing_outputs) > 0 and len(task_tests) > 0:
                    print(
                        f"\t[WARN]: Missing tests in wdl-ci.config.json for {missing_outputs} in task {task.name}"
                    )

            # Print workflow coverage for tasks with outputs and tests
            if len(workflow_tests) > 0 and len(workflow_outputs) > 0:
                workflow_coverage = (len(workflow_tests) / workflow_outputs) * 100
                if threshold is None or workflow_coverage < threshold:
                    print("-" * 150)
                    workflows_below_threshold = True
                    print(f"workflow: {wdl_filename}: {workflow_coverage:.2f}%")
                    print("-" * 150 + "\n")
        # Inform the user if no workflows matched the filter
        if workflow_name_filter is not None and not workflow_found:
            print(f"\nNo workflows found matching the filter: {workflow_name_filter}")
            sys.exit(0)
        # Warn the user about tasks that have no associated tests
        for workflow, tasks in untested_tasks.items():
            print(f"For {workflow}, these tasks are untested:")
            for task in tasks:
                print(f"\t{task}")
        # Warn the user about optional outputs that are not tested
        if len(untested_optional_outputs) > 0:
            print(
                f"\n[WARN]: These optional outputs are not tested: {untested_optional_outputs}"
            )
        else:
            print("\n✓ All optional outputs are tested")
        ## TODO: Measure is if there is a test that covered running that task with the optional input and without it
        # # Warn the user about optional inputs that are not tested
        # if untested_optional_inputs:
        #     print(
        #         f"\n[WARN]: These optional inputs are not used in any tests: {untested_optional_inputs}"
        #     )
        # else:
        #     print("\n✓ All optional inputs are tested")
        # Print a warning if any tasks or workflows are below the threshold
        if tasks_below_threshold is False:
            print(
                "\n✓ All tasks with a non-zero number of tests exceed the specified coverage threshold."
            )  ## TODO: Decide if we prefer here to specify in the print statement that untested tasks are not included, or add to the if statement to include untested tasks. expect to return if any tasks are completely untested - do see if any test has 0 coverage but also include an option to SKIP COMPLETELY UNTESTED. First step here is that untested tests DO NOT Meet the threshold --> include those in the output
        if workflows_below_threshold is False:
            print("\n✓ All workflows exceed the specified coverage threshold.")

        # Calculate and print the total coverage
        if len(all_tests) > 0 and len(all_outputs) > 0:
            total_coverage = (len(all_tests) / all_outputs) * 100
            print(f"\nTotal coverage: {total_coverage:.2f}%")

    except WdlTestCliExitException as e:
        print(f"exiting with code {e.exit_code}, message: {e.message}")
        sys.exit(e.exit_code)
