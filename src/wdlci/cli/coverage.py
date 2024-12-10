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
        config = Config.instance()

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

        # Initialize dictionary with necessary variables to help compute coverage
        coverage_state = {
            "untested_workflows": [],
            "untested_tasks": {},
            "untested_outputs": {},
            "total_output_count": 0,
            "all_tests_list": [],
        }

        #### Across all workflows found in the config, the set of outputs and their associated tasks ####

        # {worfklow_name: {task_name: {output_name: [[tests_associated_without_output]]}
        config_output_tests_dict = {}

        # Iterate over each workflow in the config file
        for workflow_name, workflow_config in config.file.workflows.items():
            # Iterate over each task in the workflow
            for task_name, task_config in workflow_config.tasks.items():
                # Iterate over each test in each task (test has two nested dicts - inputs and output_tests)
                for test_config in task_config.tests:
                    # Iterate over each output and associated tests
                    for output, test in test_config.output_tests.items():
                        # Initialize the dictionary with the workflow name if it doesn't exist
                        if workflow_name not in config_output_tests_dict:
                            config_output_tests_dict[workflow_name] = {}
                        # Initialize the nested dictionary within the workflow with the task name if it doesn't exist
                        if task_name not in config_output_tests_dict[workflow_name]:
                            config_output_tests_dict[workflow_name][task_name] = {}
                        # Initialize nested dictionary within the task dictionary with the output name if it doesn't exist
                        if (
                            output
                            not in config_output_tests_dict[workflow_name][task_name]
                        ):
                            config_output_tests_dict[workflow_name][task_name][
                                output
                            ] = []
                        # Check if 'test_tasks' key exists in the test dictionary and is not empty; if so, append the test_tasks to the output list
                        if "test_tasks" in test and test["test_tasks"]:
                            config_output_tests_dict[workflow_name][task_name][
                                output
                            ].append(test["test_tasks"])

        #### Now that we've constructed the dictionary of outputs and their associated tests using the config file, we can compare this to the WDL files ####

        # Load all WDL files in the directory
        wdl_files = find_wdl_files()
        ## TODO - do we need/want the below?
        untested_optional_outputs = []
        # Flags to track if any tasks/workflows are below the threshold and if any workflows match the filter
        tasks_below_threshold = False
        workflow_found = False
        workflows_below_threshold = False

        # Iterate over each WDL file
        for wdl_file in wdl_files:
            workflow_tests_list = []
            workflow_output_count = 0
            # Load the WDL document
            doc = WDL.load(wdl_file)
            # print(doc.workflow)
            ## if doc.workflow or len(doc.tasks) > 0:
            # if len(doc.tasks) > 0:
            #     print(f"Tasks in {wdl_file}")
            #     print(task.__dict__ for task in doc.tasks)
            # else:
            #     print(f"{wdl_file} has no tasks")
            # Check if the WDL document has >0 tasks or a workflow attribute exists; structs might be part of the config and do not have tasks nor do they have outputs to test. Additionally, just checking for tasks >0 misses parent workflows that just import and call other tasks/workflows. TBD if we want to include this, but ultimately, if there are no tasks or a workflow at all, we skip the WDL file
            if len(doc.tasks) > 0 or doc.workflow:
                # If workflow_name_filter is provided, skip all other workflows
                if doc.workflow and workflow_name_filter:
                    if workflow_name_filter not in doc.workflow.name:
                        continue
                    workflow_found = True

                # Iterate over each task in the WDL document
                for task in doc.tasks:
                    # Set the workflow name as the workflow name in the WDL file if it exists, otherwise set it to the task name as this handles the case where there is no workflow block in the WDL file (i.e., it's a single task WDL file)
                    workflow_name = doc.workflow.name if doc.workflow else task.name
                    # Add to counters for total output count and workflow output count
                    coverage_state["total_output_count"] += len(task.outputs)
                    workflow_output_count += len(task.outputs)
                    try:
                        # Create a list of dictionaries for each set of task tests in our config file
                        task_tests = (
                            config._file.workflows[wdl_file].tasks[task.name].tests
                        )

                        # We are reducing the set of tested_outputs (output names) across input sets for the same task, ie if the same output is tested multiple times with different inputs, we'll count it as tested
                        # TODO: consider that different behaviour may be desired (eg for tasks with optional inputs (and/or outputs?), we probably want to confirm that there are at least 2 tests for each output: one where the optional input is defined, one where it isn't

                        # Create a list of all the outputs that are tested in the config file and found in the task output_tests dictionary; duplicates are removed
                        tested_outputs = list(
                            set(
                                [
                                    output_name
                                    for test in task_tests
                                    for output_name in test.output_tests.keys()
                                ]
                            )
                        )
                        # Create a list of all the outputs that are present in the tas
                        all_task_outputs = [output.name for output in task.outputs]

                        # Create a list of outputs that are present in the task but not in the config file
                        missing_outputs = [
                            output_name
                            for output_name in all_task_outputs
                            if output_name not in tested_outputs
                        ]

                        # Add tested outputs to workflow_tests_list and all_tests_list
                        workflow_tests_list.extend(tested_outputs)
                        coverage_state["all_tests_list"].extend(tested_outputs)

                        # Add missing outputs to the coverage_state dictionary under the structure {workflow_name: {task_name: {output_name: [missing_outputs]}}}
                        if workflow_name not in coverage_state["untested_outputs"]:
                            coverage_state["untested_outputs"][workflow_name] = {}
                        if (
                            task.name
                            not in coverage_state["untested_outputs"][workflow_name]
                        ):
                            coverage_state["untested_outputs"][workflow_name][
                                task.name
                            ] = missing_outputs

                        # Check for optional inputs and check if there is a test that covers running that task with the optional input and without it
                        optional_inputs = [
                            input.name for input in task.inputs if input.type.optional
                        ]
                        if len(optional_inputs) > 0:
                            outputs_missing_tests = []
                            for output_name in all_task_outputs:
                                tests_with_optional_inputs = [
                                    test
                                    for test in task_tests
                                    if any(
                                        optional_input in test.inputs
                                        for optional_input in optional_inputs
                                    )
                                ]
                                tests_without_optional_inputs = [
                                    test
                                    for test in task_tests
                                    if all(
                                        optional_input not in test.inputs
                                        for optional_input in optional_inputs
                                    )
                                ]
                                if (
                                    len(tests_with_optional_inputs) < 1
                                    or len(tests_without_optional_inputs) < 1
                                ):
                                    outputs_missing_tests.append(output_name)
                            if len(outputs_missing_tests) > 0:
                                print(
                                    f"\n\t[WARN]: Outputs {outputs_missing_tests} in task {task.name} do not have tests with and without optional inputs (optional inputs: {optional_inputs})."
                                )
                        # print(f"{task.name}")
                        # print(f"Tested outputs: {tested_outputs}")
                        # print(f"All task outputs: {all_task_outputs}")
                        # print(f"Missing outputs: {missing_outputs}")
                    # Catch the case where tasks are completely absent from the config
                    except KeyError:
                        # Initialize workflow in coverage state[untested_tasks] dict if there is a workflow in the WDL file but no tests in the config file
                        if workflow_name not in coverage_state["untested_tasks"]:
                            coverage_state["untested_tasks"][workflow_name] = []
                        # Create a list of tasks associated with the respective workflow that are not present in the config file
                        coverage_state["untested_tasks"][workflow_name].append(
                            task.name
                        )
                    # If there are outputs, untested tasks, and tests for the task, calculate the task coverage
                    if (
                        len(task.outputs) > 0
                        and len(coverage_state["untested_outputs"]) > 0
                    ):
                        if len(task_tests) > 0:
                            # Calculate and print the task coverage
                            task_coverage = (
                                len(tested_outputs) / len(task.outputs)
                            ) * 100
                            if threshold is None or task_coverage < threshold:
                                tasks_below_threshold = True
                                print(f"\ntask.{task.name}: {task_coverage:.2f}%")

                            # Warn the user about outputs that are not tested
                            if workflow_name in coverage_state["untested_outputs"]:
                                if (
                                    task.name
                                    in coverage_state["untested_outputs"][workflow_name]
                                ):
                                    missing_outputs = coverage_state[
                                        "untested_outputs"
                                    ][workflow_name][task.name]
                                    if len(missing_outputs) > 0:
                                        # Filter out tasks with no missing outputs
                                        filtered_missing_outputs = {
                                            k: v
                                            for k, v in coverage_state[
                                                "untested_outputs"
                                            ][workflow_name].items()
                                            if v
                                        }
                                        if filtered_missing_outputs:
                                            missing_outputs_list = [
                                                item
                                                for sublist in filtered_missing_outputs.values()
                                                for item in sublist
                                            ]
                                            print(
                                                f"\n\t[WARN]: Missing tests in wdl-ci.config.json for {missing_outputs_list} in task {task.name}"
                                            )

                # Calculate workflow coverage; only calculate if there are outputs and tests for the workflow. If there are no outputs or tests but there is a workflow block and name, add the workflow to the untested_workflows list
                # Need to make sure there is a valid workflow and that the workflow has a name; avoids trying to calculate coverage for struct workflows
                if (
                    workflow_output_count > 0
                    and len(workflow_tests_list) > 0
                    and doc.workflow
                    and doc.workflow.name
                ):
                    workflow_coverage = (
                        len(workflow_tests_list) / workflow_output_count
                    ) * 100
                    if threshold is None or workflow_coverage < threshold:
                        workflows_below_threshold = True
                        print("-" * 150)
                        print(
                            f"Workflow: {doc.workflow.name}: {workflow_coverage:.2f}%"
                        )
                elif (
                    workflow_output_count == 0
                    or len(workflow_tests_list) == 0
                    and doc.workflow
                    and doc.workflow.name
                ):
                    if doc.workflow.name not in coverage_state["untested_workflows"]:
                        coverage_state["untested_workflows"].append(doc.workflow.name)

        # Inform the user if no workflows matched the filter
        if workflow_name_filter and not workflow_found:
            print(f"\nNo workflows found matching the filter: {workflow_name_filter}")
            sys.exit(0)

        # Check if there are tests for each output
        # for output in task.outputs:
        #     if output.name in output_tests.keys() and len(output_tests) > 0:
        #         task_tests.append(output.name)
        #         workflow_tests.append(output.name)
        #         all_tests.append(output.name)
        #         elif (
        #             output.type.optional
        #             and output.name not in output_tests.keys()
        #             or (
        #                 output.name in output_tests.keys()
        #                 and len(output_tests[output.name]) == 0
        #             )
        #         ):
        #             untested_optional_outputs.append(output.name)

        #             )
        # # Warn the user about optional outputs that are not tested
        # if len(untested_optional_outputs) > 0:
        #     print(
        #         f"\n[WARN]: These optional outputs are not tested: {untested_optional_outputs}"
        #     )
        # else:
        #     print("\n✓ All optional outputs are tested")

        if (
            tasks_below_threshold is False
            and len(coverage_state["untested_tasks"]) == 0
        ):
            print("\n✓ All tasks exceed the specified coverage threshold.")
        elif len(coverage_state["untested_tasks"]) > 0:
            print("\n[WARN]: The following tasks have no tests:")
            for workflow, tasks in coverage_state["untested_tasks"].items():
                for task in tasks:
                    print(f"\t{workflow}.{task}")

        # Check if any workflows are below the threshold and there are no untested workflows; if so return to the user that all workflows exceed the threshold
        if (
            workflows_below_threshold is False
            and len(coverage_state["untested_workflows"]) == 0
        ):
            print("\n✓ All workflows exceed the specified coverage threshold.")

        # If there are any workflows that are below the threshold, warn the user. Include a check for the workflow_name_filter to ensure that only the specified workflow is printed if a filter is provided
        else:
            if (
                workflow_name_filter in coverage_state["untested_workflows"]
                or workflow_name_filter is None
                and len(coverage_state["untested_workflows"]) > 0
            ):
                print("\n[WARN]: The following workflows have no tests:")
                for workflow in coverage_state["untested_workflows"]:
                    print(f"\t{workflow}")

        # Calculate and print the total coverage
        if (
            len(coverage_state["all_tests_list"]) > 0
            and coverage_state["total_output_count"] > 0
            and not workflow_name_filter
        ):
            total_coverage = (
                len(coverage_state["all_tests_list"])
                / coverage_state["total_output_count"]
            ) * 100
            print(f"\nTotal coverage: {total_coverage:.2f}%")

    except WdlTestCliExitException as e:
        print(f"exiting with code {e.exit_code}, message: {e.message}")
        sys.exit(e.exit_code)
