import WDL
import os
import sys

from wdlci.config import Config
from wdlci.exception.wdl_test_cli_exit_exception import WdlTestCliExitException
from wdlci.utils.initialize_worklows_and_tasks import find_wdl_files

# TODO: add structure of all dicts as comments for clarity once dev is complete e.g., # {wdl_file_name: [task_name]}


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

        # Initialize dictionary of necessary variables to compute coverage; aims to mimic config file structure
        coverage_state = {
            "untested_tasks": {},
            "total_output_count": 0,
            "all_tests_list": [],
        }
        # print(config.__dict__)
        # print(config._file)
        # print(config._file.__dict__.keys())
        # print(config._file.workflows.keys())
        # for workflow in config.file.workflows.keys():
        #     print(f"Workflow: {workflow}")
        #     doc = WDL.load(workflow)
        #     task = doc.tasks[0]
        #     print(f"Task: {task.__dict__.keys()}")
        #     print(f"Task: {task.name}")
        #     output = task.outputs[0]
        #     print(output.__dict__.keys())
        #     print(f"Output: {output.name}")
        #     tests = config.file.workflows[workflow].tasks[task.name].tests
        #     for test in tests:
        #         print(test)

        #     raise SystemExit()

        #### Across all wdl files in the config, the set of outputs and their associated tasks ####

        # {worfklow_name: {output_name: [tests_associated_without_output]}
        output_tests = {}

        # Iterate over each workflow in the config file
        for workflow_name, workflow_config in config.file.workflows.items():
            # Iterate over each task in the workflow
            for task_name, task_config in workflow_config.tasks.items():
                # Iterate over each test in each task (test has two nested dicts - inputs and output_tests)
                for test_config in task_config.tests:
                    # Iterate over each output and associated tests
                    for output, test in test_config.output_tests.items():
                        # Add the output to the dictionary for the current workflow if it is not already present
                        if workflow_name not in output_tests:
                            output_tests[workflow_name] = {}
                        if task_name not in output_tests[workflow_name]:
                            output_tests[workflow_name][task_name] = {}
                        if output not in output_tests[workflow_name][task_name]:
                            output_tests[workflow_name][task_name][output] = []
                        # Check if 'test_tasks' key exists in the test dictionary and is not empty and append to output_tests if present and not empty
                        if "test_tasks" in test and test["test_tasks"]:
                            output_tests[workflow_name][task_name][output].append(
                                test["test_tasks"]
                            )

        # Load all WDL files in the directory
        wdl_files = find_wdl_files()
        # Initialize counters/lists
        # total_output_count = 0
        # all_tests = []
        # # For each wdl file, the set of tasks that do not have any tests associated
        # # {wdl_file_name: [task_name]}
        # untested_tasks = {}
        untested_optional_outputs = []
        # Flags to track if any tasks/workflows are below the threshold and if any workflows match the filter
        tasks_below_threshold = False
        workflows_below_threshold = False
        workflow_found = False

        # Iterate over each WDL file
        for wdl_file in wdl_files:
            workflow_tests_list = []
            workflow_output_count = 0
            # Strip everything except workflow name
            wdl_filename = wdl_file.split("/")[-1]
            # Load the WDL document
            doc = WDL.load(wdl_file)

            # If workflow_name_filter is provided, skip all other workflows
            if (
                workflow_name_filter is not None
                and workflow_name_filter not in wdl_filename
            ):
                continue
            workflow_found = True

            # Iterate over each task in the WDL document
            for task in doc.tasks:
                try:
                    task_tests = config._file.workflows[wdl_file].tasks[task.name].tests
                    # print([test.__dict__ for test in task_tests])
                    # we are reducing the set of tested_outputs (output names) across input sets for the same task, ie if the same output is tested multiple times with different inputs, we'll count it as tested
                    # TODO: consider that different behaviour may be desired (eg for tasks with optional inputs (and/or outputs?), we probably want to confirm that there are at least 2 tests for each output: one where the optional input is defined, one where it isn't
                    tested_outputs = list(
                        set(
                            [
                                output_name
                                for test in task_tests
                                for output_name in test.output_tests.keys()
                            ]
                        )
                    )
                    all_task_outputs = [output.name for output in task.outputs]
                    missing_outputs = [
                        output_name
                        for output_name in all_task_outputs
                        if output_name not in tested_outputs
                    ]
                    print(f"Tested outputs: {tested_outputs}")
                    print(f"All task outputs: {all_task_outputs}")
                    print(f"Missing outputs: {missing_outputs}")
                except KeyError:
                    # Create a list of outputs that are present in the task/worfklow but not in the config JSON using the output_tests dictionary
                    outputs_present_in_workflow_absent_in_config = [
                        output.name
                        for output in task.outputs
                        if output.name not in output_tests.keys()
                        or output.name in output_tests.keys()
                        and not output_tests[output.name]
                    ]
                    print(outputs_present_in_workflow_absent_in_config)
        raise SystemExit

        ## TODO: haven't worked on the below yet - not to say the above is complete, but it's moving in the right direction

        # Count the number of outputs for the task
        #         coverage_state["total_output_count"] += len(task.outputs)
        #         workflow_output_count += len(task.outputs)

        #         # Check if there are tests for each output
        #         for output in task.outputs:
        #             if output.name in output_tests.keys() and len(output_tests) > 0:
        #                 task_tests.append(output.name)
        #                 workflow_tests.append(output.name)
        #                 all_tests.append(output.name)
        #             elif (
        #                 output.type.optional
        #                 and output.name not in output_tests.keys()
        #                 or (
        #                     output.name in output_tests.keys()
        #                     and len(output_tests[output.name]) == 0
        #                 )
        #             ):
        #                 untested_optional_outputs.append(output.name)
        #         # Print task coverage for tasks with outputs and tests
        #         if len(task.outputs) > 0 and len(task_tests) > 0:
        #             # Calculate and print the task coverage
        #             task_coverage = (len(task_tests) / len(task.outputs)) * 100
        #             if threshold is None or task_coverage < threshold:
        #                 tasks_below_threshold = True
        #                 print(f"task.{task.name}: {task_coverage:.2f}%")
        #         # If there are outputs but no tests for the entire task, add the task to the untested_tasks list
        #         elif (
        #             len(task.outputs) > 0 and not task_tests
        #         ):  # Consider building this into the above so that we can incorporate untested tasks into the threshold check/statement returned to user
        #             if wdl_filename not in untested_tasks:
        #                 untested_tasks[wdl_filename] = []
        #             untested_tasks[wdl_filename].append(task.name)
        #         if len(missing_outputs) > 0 and len(task_tests) > 0:
        #             print(
        #                 f"\t[WARN]: Missing tests in wdl-ci.config.json for {missing_outputs} in task {task.name}"
        #             )

        #     # Print workflow coverage for tasks with outputs and tests
        #     if len(workflow_tests) > 0 and workflow_outputs > 0:
        #         workflow_coverage = (len(workflow_tests) / workflow_outputs) * 100
        #         if threshold is None or workflow_coverage < threshold:
        #             print("-" * 150)
        #             workflows_below_threshold = True
        #             print(f"workflow: {wdl_filename}: {workflow_coverage:.2f}%")
        #             print("-" * 150 + "\n")
        # # Inform the user if no workflows matched the filter
        # if workflow_name_filter is not None and not workflow_found:
        #     print(f"\nNo workflows found matching the filter: {workflow_name_filter}")
        #     sys.exit(0)
        # # Warn the user about tasks that have no associated tests
        # for workflow, tasks in untested_tasks.items():
        #     print(f"For {workflow}, these tasks are untested:")
        #     for task in tasks:
        #         print(f"\t{task}")
        # # Warn the user about optional outputs that are not tested
        # if len(untested_optional_outputs) > 0:
        #     print(
        #         f"\n[WARN]: These optional outputs are not tested: {untested_optional_outputs}"
        #     )
        # else:
        #     print("\n✓ All optional outputs are tested")
        # ## TODO: Measure is if there is a test that covered running that task with the optional input and without it
        # # # Warn the user about optional inputs that are not tested
        # # if untested_optional_inputs:
        # #     print(
        # #         f"\n[WARN]: These optional inputs are not used in any tests: {untested_optional_inputs}"
        # #     )
        # # else:
        # #     print("\n✓ All optional inputs are tested")
        # # Print a warning if any tasks or workflows are below the threshold
        # if tasks_below_threshold is False:
        #     print(
        #         "\n✓ All tasks with a non-zero number of tests exceed the specified coverage threshold."
        #     )  ## TODO: User would expect to return if any tasks are completely untested - do see if any test has 0 coverage but also include an option to SKIP COMPLETELY UNTESTED. First step here is that untested tests DO NOT Meet the threshold --> include those in the output; add option to skip seeing completely untested tasks
        # if workflows_below_threshold is False:
        #     print("\n✓ All workflows exceed the specified coverage threshold.")

        # # Calculate and print the total coverage
        # if len(all_tests) > 0 and total_output_count > 0:
        #     total_coverage = (len(all_tests) / total_output_count) * 100
        #     print(f"\nTotal coverage: {total_coverage:.2f}%")

    except WdlTestCliExitException as e:
        print(f"exiting with code {e.exit_code}, message: {e.message}")
        sys.exit(e.exit_code)
