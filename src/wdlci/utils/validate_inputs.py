from wdlci.exception.wdl_test_cli_exit_exception import WdlTestCliExitException


def validate_inputs(test_key, task, input_dict):
    workflow_task_split = test_key.replace("-", " - ")

    # Confirm that all required inputs have been set
    non_optional_task_inputs = [
        task.name for task in task.inputs if not task.type._optional and not task.expr
    ]
    missing_inputs = [
        task_input
        for task_input in non_optional_task_inputs
        if task_input not in input_dict
    ]

    if len(missing_inputs) > 0:
        raise WdlTestCliExitException(
            f"Required inputs for test case [{workflow_task_split}] not set:\n{missing_inputs}",
            1,
        )

    # Remove inputs that are not required
    expected_task_inputs = [task.name for task in task.inputs]
    for task_input in list(input_dict):
        if task_input not in expected_task_inputs:
            print(
                f"\t[WARN] detected extra input [{task_input}] for test case [{workflow_task_split}]; ignoring"
            )
            del input_dict[task_input]

    return input_dict
