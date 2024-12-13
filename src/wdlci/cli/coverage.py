import WDL
import os
import sys

from wdlci.config import Config
from wdlci.exception.wdl_test_cli_exit_exception import WdlTestCliExitException
from wdlci.utils.initialize_worklows_and_tasks import find_wdl_files

# Initialize dictionary with necessary variables to compute coverage
coverage_summary = {
    "untested_workflows": [],
    # {workflow_name: [task_name]}
    "untested_tasks": {},
    # {workflow_name: {task_name: [output_name]}}
    "untested_outputs": {},
    # {workflow_name: {task_name: [output_name]}}
    "untested_outputs_with_optional_inputs": {},
    ## TODO: TBD if the tested_outputs nested dict is necessary - maybe some nuance with the calculations I'm missing right now; case where  outputs in different workflows or tasks that share a name (e.g. vcf as an output from glnexus and deepvariant
    # {workflow_name: {task_name: [output_name]}}
    "tested_outputs_dict": {},
    "total_output_count": 0,
    "all_tests_list": [],
    "skipped_workflows": [],
}


def coverage_handler(kwargs):
    threshold = kwargs["target_coverage"]
    workflow_name_filter = kwargs["workflow_name"]
    print(f"Target coverage threshold: ", threshold)
    if workflow_name_filter:
        print(f"Workflow name filter: {workflow_name_filter}\n")
    else:
        print("Workflow name filter: None\n")
    print("┍━━━━━━━━━━━━━┑")
    print("│   Coverage  │")
    print("┕━━━━━━━━━━━━━┙")
    try:
        # Load the config file
        Config.load(kwargs)
        config = Config.instance()

        # Load all WDL files in the directory
        wdl_files = find_wdl_files()

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

            # Handle the case where the WDL file is not in the configuration but is present in the directory
            if wdl_file not in config._file.workflows:
                coverage_summary["skipped_workflows"].append(wdl_file)
                continue

            # Now that we know the WDL file is in the configuration, we can set the workflow name from the WDL.Tree.Document workflow attribute if it exists, otherwise we can grab the workflow name from the key from the configuration file as single task WDL files do not have a workflow attribute and some workflows have no tasks. This also helps organize the coverage output when we have a WDL file with >1 task but no workflow block (e.g., https://github.com/PacificBiosciences/wdl-common/blob/main/wdl/tasks/samtools.wdl), so that each task from the WDL file is grouped under the WDL file name regardless if it's defined as a workflow or not
            workflow_name = (
                doc.workflow.name
                if doc.workflow
                else os.path.basename(config._file.workflows[wdl_file].key).replace(
                    ".wdl", ""
                )
            )

            # Check if the WDL document has > 0 tasks or a workflow attribute exists; structs might be part of the config and do not have tasks nor do they have outputs to test. Additionally, just checking for > 0 tasks misses parent workflows that just import and call other tasks/workflows. TBD if we want to include these 'parent' workflows, but ultimately, if there are no tasks or a workflow attribute, we skip the WDL file and print a warning
            if len(doc.tasks) > 0 or doc.workflow:
                # If workflow_name_filter is provided, skip all other workflows
                if (
                    workflow_name_filter is not None
                    and workflow_name_filter not in workflow_name
                ):
                    continue
                workflow_found = True

                # Iterate over each task in the WDL document
                for task in doc.tasks:
                    # Add to counters for total output count and workflow output count
                    coverage_summary["total_output_count"] += len(task.outputs)
                    workflow_output_count += len(task.outputs)
                    # Initialize a list of task test dictionaries
                    task_tests_list = []
                    try:
                        # Create a list of dictionaries for each set of task tests in our config file
                        task_tests_list = (
                            config._file.workflows[wdl_file].tasks[task.name].tests
                        )

                        # We are reducing the set of tested_outputs (output names) across input sets for the same task, ie if the same output is tested multiple times with different inputs, we'll count it as tested
                        # Create a list of all the outputs that are tested in the config file and found in the task output_tests dictionary; duplicates are removed
                        tested_outputs = list(
                            set(
                                [
                                    output_name
                                    for test in task_tests_list
                                    for output_name in test.output_tests.keys()
                                ]
                            )
                        )

                        _update_coverage_summary(
                            "tested_outputs_dict",
                            workflow_name,
                            task.name,
                            output_names=tested_outputs,
                        )

                        # Create a list of all the outputs that are present in the task
                        all_task_outputs = [output.name for output in task.outputs]

                        # Create a list of outputs that are present in the task but not in the config file
                        missing_outputs = [
                            output_name
                            for output_name in all_task_outputs
                            if output_name not in tested_outputs
                        ]

                        # Add tested outputs to workflow_tests_list and all_tests_list
                        workflow_tests_list.extend(tested_outputs)
                        coverage_summary["all_tests_list"].extend(tested_outputs)

                        # Add missing outputs to the coverage_summary[untested_outputs] dictionary
                        _update_coverage_summary(
                            "untested_outputs",
                            workflow_name,
                            task.name,
                            output_names=missing_outputs,
                        )

                        # Check for optional inputs and check if there is a test that covers running that task with the optional input and without it
                        optional_inputs = [
                            input.name for input in task.inputs if input.type.optional
                        ]
                        outputs_where_optional_inputs_not_dually_tested = []
                        if len(optional_inputs) > 0:
                            for output_name in all_task_outputs:
                                (
                                    tests_with_optional_inputs,
                                    tests_without_optional_inputs,
                                ) = _check_optional_inputs(
                                    task_tests_list, optional_inputs
                                )
                                if (
                                    len(tests_with_optional_inputs) < 1
                                    or len(tests_without_optional_inputs) < 1
                                ):
                                    outputs_where_optional_inputs_not_dually_tested.append(
                                        output_name
                                    )
                                    _update_coverage_summary(
                                        "untested_outputs_with_optional_inputs",
                                        workflow_name,
                                        task.name,
                                        output_names=outputs_where_optional_inputs_not_dually_tested,
                                    )

                    # Catch the case where tasks are completely absent from the config
                    except KeyError:
                        # Initialize workflow in coverage state[untested_tasks] dict if there is a workflow in the WDL file but no tests in the config file
                        _update_coverage_summary(
                            "untested_tasks", workflow_name, task.name
                        )

                    # If there are outputs but no tests, add the task to the untested_tasks list. If there are outputs and tests, calculate the task coverage
                    if len(task.outputs) > 0:
                        # Handle the case where the task is in the config but has no associated tests
                        if len(task_tests_list) == 0:
                            _update_coverage_summary(
                                "untested_tasks", workflow_name, task.name
                            )
                        else:
                            # Calculate and print the task coverage
                            task_coverage = (
                                len(tested_outputs) / len(task.outputs)
                            ) * 100
                            if threshold is not None and task_coverage < threshold:
                                tasks_below_threshold = True
                                print(f"\ntask.{task.name}: {task_coverage:.2f}%")
                            else:
                                print(f"\ntask.{task.name}: {task_coverage:.2f}%")

                # Calculate workflow coverage; only calculate if there are outputs and tests for the workflow. If there are no outputs or tests but there is a workflow block and name, add the workflow to the untested_workflows list
                # Need to make sure there is a valid workflow and that the workflow has a name; avoids trying to calculate coverage for struct workflows
                if workflow_output_count > 0 and len(workflow_tests_list) > 0:
                    workflow_coverage = (
                        len(workflow_tests_list) / workflow_output_count
                    ) * 100
                    if threshold is not None and workflow_coverage < threshold:
                        workflows_below_threshold = True
                        # print("-" * 150)
                        print(
                            f"\n"
                            + f"\033[34mWorkflow: {workflow_name}: {workflow_coverage:.2f}%\033[0m"
                        )
                        print("-" * 150)
                    else:
                        # print("-" * 150)
                        print(
                            f"\n"
                            + f"\033[34mWorkflow: {workflow_name}: {workflow_coverage:.2f}%\033[0m"
                        )
                        print("-" * 150)
                elif (
                    workflow_output_count == 0
                    or len(workflow_tests_list) == 0
                    and workflow_name
                ):
                    if workflow_name not in coverage_summary["untested_workflows"]:
                        coverage_summary["untested_workflows"].append(workflow_name)

            # Append the workflow to the skipped_workflows list if there are no tasks or workflow blocks
            else:
                coverage_summary["skipped_workflows"].append(wdl_file)
        # Calculate and print the total coverage
        if (
            len(coverage_summary["all_tests_list"]) > 0
            and coverage_summary["total_output_count"] > 0
            and not workflow_name_filter
        ):
            total_coverage = (
                len(coverage_summary["all_tests_list"])
                / coverage_summary["total_output_count"]
            ) * 100
            print("\n" + f"\033[33mTotal coverage: {total_coverage:.2f}%\033[0m")

        # Inform the user if no workflows matched the filter and exit
        if workflow_name_filter and not workflow_found:
            print(f"\nNo workflows found matching the filter: {workflow_name_filter}")
            sys.exit(0)

        # Sum the total number of untested outputs and untested outputs with optional inputs where there is not a test for the output with and without the optional input
        total_untested_outputs = _sum_outputs(coverage_summary, "untested_outputs")
        total_untested_outputs_with_optional_inputs = _sum_outputs(
            coverage_summary, "untested_outputs_with_optional_inputs"
        )

        # Check if any outputs are below the threshold and there are no untested outputs; if so return to the user that all outputs exceed the threshold
        print("\n┍━━━━━━━━━━━━━┑")
        print("│  Warning(s) │")
        print("┕━━━━━━━━━━━━━┙")
        if _check_threshold(tasks_below_threshold, total_untested_outputs, threshold):
            print("\n✓ All outputs exceed the specified coverage threshold.")

        if total_untested_outputs > 0:
            print("\n" + "\033[31m[WARN]: The following outputs have no tests:\033[0m")
            _print_untested_items(coverage_summary, "untested_outputs")

        if total_untested_outputs_with_optional_inputs > 0:
            # TODO: Would it be a requirement to report what input is optional here?
            print(
                "\n"
                + "\033[31m[WARN]: The following outputs are not covered by tests that include and exclude optional inputs:\033[0m"
            )
            _print_untested_items(
                coverage_summary, "untested_outputs_with_optional_inputs"
            )

        # Warn the user if any workflows were skipped
        if len(coverage_summary["skipped_workflows"]) > 0:
            print(
                "\n"
                + "\033[31m[WARN]: The following workflows were skipped as they were not found in the wdl-ci.config.json but are present in the directory or they were present in the config JSON had no tasks or workflow blocks:\033[0m"
            )
            for workflow in coverage_summary["skipped_workflows"]:
                print(f"\t{workflow}")

        # Check if any tasks are below the threshold and there are no untested tasks; if so return to the user that all tasks exceed the threshold
        if _check_threshold(
            tasks_below_threshold, len(coverage_summary["untested_tasks"]), threshold
        ):
            print("\n✓ All tasks exceed the specified coverage threshold.")
        if len(coverage_summary["untested_tasks"]) > 0:
            print("\n" + "\033[31m[WARN]: The following tasks have no tests:\033[0m")
            for workflow, tasks in coverage_summary["untested_tasks"].items():
                for task in tasks:
                    print(f"\t{workflow}.{task}")

        # Check if any workflows are below the threshold and there are no untested workflows; if so return to the user that all workflows exceed the threshold
        if _check_threshold(
            workflows_below_threshold,
            len(coverage_summary["untested_workflows"]),
            threshold,
        ):
            print("\n✓ All workflows exceed the specified coverage threshold.")

        # If there are any workflows that are below the threshold, warn the user. Include a check for the workflow_name_filter to ensure that only the specified workflow is printed if a filter is provided
        else:
            if (
                workflow_name_filter in coverage_summary["untested_workflows"]
                or workflow_name_filter is None
                and len(coverage_summary["untested_workflows"]) > 0
            ):
                print(
                    "\n"
                    + "\033[31m[WARN]: The following workflows have outputs but no tests:\033[0m"
                )
                for workflow in coverage_summary["untested_workflows"]:
                    print(f"\t{workflow}")

    except WdlTestCliExitException as e:
        print(f"exiting with code {e.exit_code}, message: {e.message}")
        sys.exit(e.exit_code)


# Helper functions
def _check_optional_inputs(task_tests_list, optional_inputs):
    tests_with_optional_inputs = [
        test
        for test in task_tests_list
        if any(optional_input in test.inputs for optional_input in optional_inputs)
    ]
    tests_without_optional_inputs = [
        test
        for test in task_tests_list
        if all(optional_input not in test.inputs for optional_input in optional_inputs)
    ]
    return tests_with_optional_inputs, tests_without_optional_inputs


def _sum_outputs(coverage_summary, key):
    return sum(
        len(outputs)
        for tasks in coverage_summary[key].values()
        for outputs in tasks.values()
    )


def _update_coverage_summary(key, workflow_name, task_name, **kwargs):
    output_names = kwargs.get("output_names", [])
    if workflow_name not in coverage_summary[key]:
        coverage_summary[key][workflow_name] = {}
    if task_name not in coverage_summary[key][workflow_name]:
        if len(output_names) > 0:
            coverage_summary[key][workflow_name][task_name] = output_names
        else:
            coverage_summary[key][workflow_name][task_name] = []


def _print_untested_items(coverage_summary, key):
    for workflow, tasks in coverage_summary[key].items():
        for task, outputs in tasks.items():
            if len(outputs) > 0:
                print(f"\t{workflow}.{task}: {outputs}")


def _check_threshold(below_threshold_flag, untested_count, threshold):
    return (
        below_threshold_flag is False and untested_count == 0 and threshold is not None
    )
