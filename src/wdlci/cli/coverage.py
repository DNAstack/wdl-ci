import WDL
import os
import sys

from wdlci.config import Config
from wdlci.exception.wdl_test_cli_exit_exception import WdlTestCliExitException
from wdlci.utils.initialize_worklows_and_tasks import find_wdl_files


def coverage_handler(kwargs):
    # Initialize dictionary with necessary variables to compute coverage
    coverage_summary = {
        "untested_workflows_list": [],
        # {workflow_name: [task_name]}
        "untested_tasks_dict": {},
        # {workflow_name: {task_name: [output_name]}}
        "untested_outputs_dict": {},
        # {workflow_name: {task_name: [output_name]}}
        "untested_outputs_with_optional_inputs_dict": {},
        # {workflow_name: {task_name: [output_name]}}
        "tested_outputs_dict": {},
        "all_outputs_list": [],
        "all_tested_outputs_list": [],
        "skipped_workflows_list": [],
    }

    threshold = kwargs["target_coverage"]
    workflow_name_filters = kwargs["workflow_name"]
    print(f"Target coverage threshold: ", threshold)
    print(f"Workflow name filters: {workflow_name_filters}\n")

    # TODO come back to this; compute on the fly at the end?
    tasks_below_threshold = False
    workflows_below_threshold = False

    print("┍━━━━━━━━━━━━━┑")
    print("│   Coverage  │")
    print("┕━━━━━━━━━━━━━┙")
    try:
        # Load the config file
        Config.load(kwargs)
        config = Config.instance()

        # Load all WDL files in the directory
        wdl_files = find_wdl_files()

        wdl_files_filtered = []
        if len(workflow_name_filters) > 0:
            for workflow_name in workflow_name_filters:
                if workflow_name in wdl_files:
                    wdl_files_filtered.append(workflow_name)
                else:
                    raise WdlTestCliExitException(
                        f"No workflows found matching the filter: [{workflow_name}]. Possible workflow options are:\n{wdl_files}",
                        1,
                    )
        else:
            wdl_files_filtered = [workflow_name for workflow_name in wdl_files]

        # Iterate over each WDL file
        for workflow_name in wdl_files_filtered:
            workflow_tested_outputs_list = []
            workflow_outputs_list = []

            # Handle the case where the WDL file is not in the configuration but is present in the directory
            if workflow_name not in config._file.workflows:
                coverage_summary["skipped_workflows_list"].append(workflow_name)
                continue

            # Load the WDL document
            doc = WDL.load(workflow_name)

            ## TODO: Ensure we handle the case where there are tasks AND imports, case with >1 imports, case with nested imports

            # If the WDL document has imports
            ## TODO: this is only recursing a single level, e.g., family importing upstream will not lead to all outputs from upstream being reported, but tertiary will work as it only has a single level of imports
            if len(doc.imports) > 0:
                for wdl_import in doc.imports:
                    #         _process_imports(
                    #             wdl_import,
                    #             coverage_summary,
                    #             config,
                    #             workflow_outputs_list,
                    #             workflow_tested_outputs_list,
                    #             threshold,
                    #         )

                    # This handles the case where the import has tasks or imported workflows that have no tasks and only import as well (e.g., family.wdl imports upstream.wdl which also just imports other tasks/workflows). It will exclude imported workflows that don't have a workflow attribute or tasks (e.g., structs)
                    if (
                        len(wdl_import.doc.tasks) > 0
                        or wdl_import.doc.workflow is not None
                    ):
                        # Iterate over each import's set of tasks and extend outputs
                        for imported_task in wdl_import.doc.tasks:
                            # Use the imports URI to populate the task_tests_list properly
                            ## TODO: definitely not ideal handling as it assumes there is a parent workflows directory -- find a better approach
                            import_workflow_name = "workflows/" + wdl_import.uri.strip(
                                "../*"
                            )
                            workflow_outputs_list.extend(
                                [output.name for output in imported_task.outputs]
                            )
                            coverage_summary["all_outputs_list"].extend(
                                [output.name for output in imported_task.outputs]
                            )

                            coverage_summary = _update_coverage(
                                coverage_summary,
                                config,
                                import_workflow_name,
                                imported_task,
                                workflow_tested_outputs_list,
                                threshold,
                            )

            # Check if the WDL document has tasks
            if len(doc.tasks) > 0:
                # Iterate over each task in the WDL document
                for task in doc.tasks:
                    # Check if the task name is present in any workflow dictionary and skip if so
                    task_present = any(
                        task.name in workflow_dict.keys()
                        for workflow_dict in coverage_summary[
                            "tested_outputs_dict"
                        ].values()
                    )

                    ## TODO: below needs testing to make sure works as intended when scaling up config -- this is not working perfectly
                    if task_present:
                        print(f"{task.name} already in dict; is being skipped")
                        continue
                    else:
                        # Add outputs to all_outputs_list and add to workflow output count
                        coverage_summary["all_outputs_list"].extend(
                            [output.name for output in task.outputs]
                        )
                        workflow_outputs_list.extend(
                            [output.name for output in task.outputs]
                        )

                        _update_coverage(
                            coverage_summary,
                            config,
                            workflow_name,
                            task,
                            workflow_tested_outputs_list,
                            threshold,
                        )

            # Calculate workflow coverage; only calculate if there are outputs and tests for the workflow. If there are no outputs or tests but there is a workflow block and name, add the workflow to the untested_workflows list
            # Need to make sure there is a valid workflow and that the workflow has a name; avoids trying to calculate coverage for struct workflows
            if len(workflow_outputs_list) > 0 and len(workflow_tested_outputs_list) > 0:
                workflow_coverage = (
                    len(workflow_tested_outputs_list) / len(workflow_outputs_list)
                ) * 100
                if threshold is not None and workflow_coverage < threshold:
                    workflows_below_threshold = True
                print(
                    f"\n"
                    + f"\033[34mWorkflow: {workflow_name}: {workflow_coverage:.2f}%\033[0m"
                )
                print("-" * 150)
            elif (
                len(workflow_outputs_list) == 0
                or len(workflow_tested_outputs_list) == 0
            ):
                coverage_summary["untested_workflows_list"].append(workflow_name)
        # Calculate and print the total coverage
        if (
            len(coverage_summary["all_tested_outputs_list"]) > 0
            and len(coverage_summary["all_outputs_list"]) > 0
        ):
            total_coverage = (
                len(coverage_summary["all_tested_outputs_list"])
                / len(coverage_summary["all_outputs_list"])
            ) * 100
            print("\n" + f"\033[33mTotal coverage: {total_coverage:.2f}%\033[0m")
        else:
            print("There are no outputs to compute coverage for.")

        # Sum the total number of untested outputs and untested outputs with optional inputs where there is not a test for the output with and without the optional input
        total_untested_outputs = _sum_outputs(coverage_summary, "untested_outputs_dict")
        total_untested_outputs_with_optional_inputs = _sum_outputs(
            coverage_summary, "untested_outputs_with_optional_inputs_dict"
        )
        total_tested_outputs = _sum_outputs(coverage_summary, "tested_outputs_dict")
        if total_tested_outputs > 0:
            print("\n The following outputs are tested:")
            _print_coverage_items(coverage_summary, "tested_outputs_dict")

        # Check if any outputs are below the threshold and there are no untested outputs; if so return to the user that all outputs exceed the threshold

        ## TODO: the below doesn't get printed because the output from the task that is imported is double counted in total tested outputs but not in all outputs list - can either double count in both or adjust the way that tested outputs are constructed in general -- TBD.
        ## TODO: confirm numbers look correct once other todos are addressed
        print(total_tested_outputs)
        print(len(coverage_summary["all_outputs_list"]))

        if total_tested_outputs == len(coverage_summary["all_outputs_list"]):
            print("\n✓ All outputs are tested.")

        if (
            total_untested_outputs > 0
            or total_untested_outputs_with_optional_inputs > 0
            or len(coverage_summary["untested_tasks_dict"]) > 0
            or len(coverage_summary["untested_workflows_list"]) > 0
            or len(coverage_summary["skipped_workflows_list"])
        ):
            print("┍━━━━━━━━━━━━━┑")
            print("│  Warning(s) │")
            print("┕━━━━━━━━━━━━━┙")

        # Warn the user if any outputs have no tests
        if total_untested_outputs > 0:
            print("\n" + "\033[31m[WARN]: The following outputs have no tests:\033[0m")
            _print_coverage_items(coverage_summary, "untested_outputs_dict")

        # Warn the user if any outputs are part of a task that contains an optional input and are not covered by at least two tests (one for each case where the optional input is and is not provided)
        if total_untested_outputs_with_optional_inputs > 0:
            print(
                "\n"
                + "\033[31m[WARN]: The following outputs are part of a task that contains an optional input and are not covered by at least two tests; they should be covered for both cases where the optional input is and is not provided:\033[0m"
            )
            _print_coverage_items(
                coverage_summary, "untested_outputs_with_optional_inputs_dict"
            )

        # Check if any tasks are below the threshold and there are no untested tasks; if so, return to the user that all tasks exceed the threshold
        if _check_threshold(
            tasks_below_threshold,
            len(coverage_summary["untested_tasks_dict"]),
            threshold,
        ):
            print("\n✓ All tasks exceed the specified coverage threshold.")

        # Warn the user if any tasks have no tests
        if len(coverage_summary["untested_tasks_dict"]) > 0:
            print("\n" + "\033[31m[WARN]: The following tasks have no tests:\033[0m")
            for workflow, tasks in coverage_summary["untested_tasks_dict"].items():
                for task in tasks:
                    print(f"\t{workflow}.{task}")

        # Check if any workflows are below the threshold and there are no untested workflows; if so, return to the user that all workflows exceed the threshold
        if _check_threshold(
            workflows_below_threshold,
            len(coverage_summary["untested_workflows_list"]),
            threshold,
        ):
            print("\n✓ All workflows exceed the specified coverage threshold.")

        # If there are any workflows that are below the threshold, warn the user. Include a check for the workflow_name_filter to ensure that only the specified workflow is printed if a filter is provided
        else:
            if len(coverage_summary["untested_workflows_list"]) > 0:
                print(
                    "\n"
                    + "\033[31m[WARN]: The following workflows have outputs but no tests:\033[0m"
                )
                ## TODO: Need to  make sure imports aren't caught here
                for workflow in coverage_summary["untested_workflows_list"]:
                    print(f"\t{workflow}")

        # Warn the user if any workflows were skipped
        if len(coverage_summary["skipped_workflows_list"]) > 0:
            print(
                "\n"
                + "\033[31m[WARN]: The following workflows were skipped as they were not found in the wdl-ci.config.json but are present in the directory, or they were present in the config JSON had no task blocks:\033[0m"
            )
            for workflow in coverage_summary["skipped_workflows_list"]:
                print(f"\t{workflow}")

    except WdlTestCliExitException as e:
        print(f"exiting with code {e.exit_code}, message: {e.message}")
        sys.exit(e.exit_code)

    # Reset config regardless of try and except outcome - only required for running unit tests
    finally:
        config.reset()


# Helper functions
## TODO: Add docstrings and improve naming of functions that update coverage summary or combine


def _sum_outputs(coverage_summary, key):
    """
    Returns:
        (int): The number of outputs for the given category
    """
    return sum(
        len(outputs)
        for tasks in coverage_summary[key].values()
        for outputs in tasks.values()
    )


def _update_coverage_summary(coverage_summary, key, workflow_name, task_name, **kwargs):
    output_names = kwargs.get("output_names", [])
    if workflow_name not in coverage_summary[key]:
        coverage_summary[key][workflow_name] = {}
    if task_name not in coverage_summary[key][workflow_name]:
        if len(output_names) > 0:
            coverage_summary[key][workflow_name][task_name] = output_names
        else:
            coverage_summary[key][workflow_name][task_name] = []
    return coverage_summary


def _print_coverage_items(coverage_summary, key):
    for workflow, tasks in coverage_summary[key].items():
        for task, outputs in tasks.items():
            if len(outputs) > 0:
                print(f"\t{workflow}.{task}: {outputs}")


def _check_threshold(below_threshold_flag, untested_count, threshold):
    return (
        below_threshold_flag is False and untested_count == 0 and threshold is not None
    )


def _update_coverage(
    coverage_summary,
    config,
    workflow_name,
    task,
    workflow_tested_outputs_list,
    threshold,
):
    # Initialize a list of task test dictionaries
    task_tests_list = []

    # Create a list of dictionaries for each set of task tests in our config file
    task_tests_list = config._file.workflows[workflow_name].tasks[task.name].tests
    # We are reducing the set of tested_outputs (output names) across input sets for the same task, ie if the same output is tested multiple times with different inputs, we'll count it as tested
    # Create a list of all the outputs that are tested in the config file and found in the task output_tests dictionary
    tested_outputs = list(
        set(
            [
                output_name
                for test in task_tests_list
                for output_name, output_test in test.output_tests.items()
                # Handle the case where test_tasks exists but is an empty list
                if len(output_test.get("test_tasks")) > 0
            ]
        )
    )
    # Update coverage_summary with tested outputs for each task
    if len(tested_outputs) > 0:
        coverage_summary = _update_coverage_summary(
            coverage_summary,
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

    # Add tested outputs to workflow_tested_outputs_list and all_tested_outputs_list
    workflow_tested_outputs_list.extend(tested_outputs)
    coverage_summary["all_tested_outputs_list"].extend(tested_outputs)

    # Add missing outputs to the coverage_summary[untested_outputs] dictionary if there are any missing outputs
    if len(missing_outputs) > 0:
        coverage_summary = _update_coverage_summary(
            coverage_summary,
            "untested_outputs_dict",
            workflow_name,
            task.name,
            output_names=missing_outputs,
        )

    # Check for optional inputs and check if there is a test that covers running that task with the optional input and without it
    optional_inputs = [input.name for input in task.inputs if input.type.optional]
    optional_inputs_not_dually_tested = []
    for optional_input in optional_inputs:
        test_exists_with_optional_set = False
        test_exists_with_optional_not_set = False
        for task_test in task_tests_list:
            if optional_input in task_test.inputs:
                test_exists_with_optional_set = True
            else:
                test_exists_with_optional_not_set = True

        if not (test_exists_with_optional_set and test_exists_with_optional_not_set):
            optional_inputs_not_dually_tested.extend(
                [output.name for output in task.outputs]
            )

    coverage_summary = _update_coverage_summary(
        coverage_summary,
        "untested_outputs_with_optional_inputs_dict",
        workflow_name,
        task.name,
        output_names=list(set(optional_inputs_not_dually_tested)),
    )
    # If there are outputs but no tests, add the task to the untested_tasks list. If there are outputs and tests, calculate the task coverage
    if len(task.outputs) > 0:
        # Handle the case where the task is in the config but has no associated tests
        if len(task_tests_list) == 0:
            coverage_summary = _update_coverage_summary(
                coverage_summary,
                "untested_tasks_dict",
                workflow_name,
                task.name,
            )
        else:
            # Calculate and print the task coverage
            task_coverage = (
                len(coverage_summary["tested_outputs_dict"][workflow_name][task.name])
                / len(task.outputs)
            ) * 100
            if threshold is not None and task_coverage < threshold:
                tasks_below_threshold = True
                print(f"\ntask.{task.name}: {task_coverage:.2f}%")
            else:
                print(f"\ntask.{task.name}: {task_coverage:.2f}%")
    return coverage_summary


def _process_imports(
    wdl_import,
    coverage_summary,
    config,
    workflow_outputs_list,
    workflow_tested_outputs_list,
    threshold,
):
    print(f"{wdl_import.namespace} is imported")

    # Handle nested imports
    if len(wdl_import.doc.imports) > 0:
        for nested_import in wdl_import.doc.imports:
            _process_imports(
                nested_import,
                coverage_summary,
                config,
                workflow_outputs_list,
                workflow_tested_outputs_list,
                threshold,
            )

    # This handles the case where the import has tasks or imported workflows that have no tasks and only import as well (e.g., family.wdl imports upstream.wdl which also just imports other tasks/workflows). It will exclude imported workflows that don't have a workflow attribute or tasks (e.g., structs)
    if len(wdl_import.doc.tasks) > 0 or wdl_import.doc.workflow is not None:
        # Iterate over each import's set of tasks and extend outputs
        for imported_task in wdl_import.doc.tasks:
            # Use the imports URI to populate the task_tests_list properly
            ## TODO: definitely not ideal handling as it assumes there is a parent workflows directory -- find a better approach
            import_workflow_name = "workflows/" + wdl_import.uri.strip("../*")
            workflow_outputs_list.extend(
                [output.name for output in imported_task.outputs]
            )
            coverage_summary["all_outputs_list"].extend(
                [output.name for output in imported_task.outputs]
            )

            coverage_summary = _update_coverage(
                coverage_summary,
                config,
                import_workflow_name,
                imported_task,
                workflow_tested_outputs_list,
                threshold,
            )
    return coverage_summary
