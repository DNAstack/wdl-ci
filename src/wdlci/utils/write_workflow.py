import WDL
from wdlci.exception.wdl_test_cli_exit_exception import WdlTestCliExitException


def write_workflow(workflow_name, main_task, test_task, test_outputs, output_file):
    """
    Write a workflow out to a file
    Args:
        workflow_name (str): Name of the workflow (workflow entrypoint)
        main_task (WDL.Tree.Task): Task to be tested
        test_task (WDL.Tree.Task): Test task to be run on the main task
        test_outputs ({output_key: output_value}): Validated outputs to test
        output_file (str): Path to file to write workflow to
    """
    wdl_version = main_task.effective_wdl_version
    test_task_function = _get_test_task_function(test_task.name)

    main_task_output_types = {output.name: output.type for output in main_task.outputs}

    with open(output_file, "w") as f:
        f.write(f"version {wdl_version}\n\n")

        f.write(f"workflow {workflow_name} {{\n")

        ## Inputs
        f.write("\tinput " + "{\n")
        for task_input in main_task.inputs:
            f.write(f"\t\t{task_input}\n")
        f.write("\n")
        for test_output in test_outputs:
            test_output_type = main_task_output_types[test_output]
            f.write(f"\t\t{test_output_type} TEST_OUTPUT_{test_output}\n")
        f.write("\t}\n")
        f.write("\n")

        ## Call to main task
        f.write(f"\tcall {main_task.name} {{\n")
        f.write("\t\tinput:\n")
        for index, task_input in enumerate(main_task.inputs):
            trailing_comma = "" if index == len(main_task.inputs) - 1 else ","
            input_name = task_input.name
            f.write(f"\t\t\t{input_name} = {input_name}{trailing_comma}\n")
        f.write("\t}\n")
        f.write("\n")

        ## Call to test task
        _get_test_task_function(test_task.name)(f, main_task, test_task, test_outputs)

        ## Outputs
        f.write("\toutput {\n")
        for task_output in test_task.outputs:
            f.write(
                f"\t\t{task_output.type} {task_output.name} = {test_task.name}.{task_output.name}\n"
            )
        f.write("\t}\n")
        f.write("\n")

        f.write("}\n")
        f.write("\n")

    _write_task(main_task, output_file)
    _write_task(test_task, output_file)


def _get_test_task_function(task_name):
    """
    Get the function that will write the call to the test task
    Args:
        task_name (str): Test task name; used to identify the call-write function to return
    Returns:
        (fn): Function that will write the call to the requested test task to the output workflow file
    """

    def write_compare_call(f, main_task, test_task, test_outputs):
        comparisons = {"File": {}, "String": {}}

        # Map current run outputs to validated outputs for each output type
        for output in main_task.outputs:
            if output.name in test_outputs:
                current_run_output = f"{main_task.name}.{output.name}"
                validated_output = f"TEST_OUTPUT_{output.name}"
                if isinstance(output.type, WDL.Type.File):
                    comparisons["File"] = {current_run_output: validated_output}
                elif isinstance(output.type, WDL.Type.String):
                    comparisons["String"] = {current_run_output: validated_output}
                else:
                    raise WdlTestCliExitException(
                        f"Unimplemented type for comparison [{output.type}]", 1
                    )

        ## Input maps for each type
        inputs_found = False
        for input_type in comparisons:
            f.write(
                f"\tMap[{input_type},{input_type}] {input_type.lower()}_compares = {{\n"
            )
            for index, current_run_output in enumerate(comparisons[input_type]):
                separator = "," if index < (len(comparisons[input_type]) - 1) else ""
                f.write(f"\t\t{current_run_output}: {validated_output}{separator}\n")
                inputs_found = True
            f.write("\t}\n")

        if not inputs_found:
            raise WdlTestCliExitException("No outputs found to compare", 1)

        ## Call to test task
        f.write(f"\tcall {test_task.name} {{\n")
        f.write("\t\tinput:\n")
        for input_index, input_type in enumerate(comparisons):
            separator = "," if input_index < (len(comparisons) - 1) else ""
            input_name = f"{input_type.lower()}_compares"
            f.write(f"\t\t\t{input_name} = {input_name}{separator}\n")
        f.write("\t}\n\n")

    test_task_call_functions = {"compare": write_compare_call}

    if task_name not in test_task_call_functions:
        raise WdlTestCliExitException(
            f"Task {task_name} not found in {test_task_call_functions.keys()}; must define function to write the call to this test task",
            1,
        )
    return test_task_call_functions[task_name]


def _write_task(doc_task, output_file):
    """
    Write a task out to a file
    Args:
        doc_task (WDL.Tree.Task): task to write
        output_file (str): Path to file to write task to
    """
    with open(output_file, "a") as f:
        f.write(f"task {doc_task.name} {{\n")

        ## Inputs
        f.write("\tinput " + "{\n")
        for task_input in doc_task.inputs:
            f.write(f"\t\t{task_input}\n")
        f.write("\t}\n")
        f.write("\n")

        ## Post inputs
        for post_input in doc_task.postinputs:
            f.write(f"\t{post_input}\n")
        f.write("\n")

        ## Command
        f.write("\tcommand <<<\n")
        f.write(f"\t\t{doc_task.command}\n")
        f.write("\t>>>\n")
        f.write("\n")

        ## Outputs
        f.write("\toutput {\n")
        for task_output in doc_task.outputs:
            f.write(f"\t\t{task_output}\n")
        f.write("\t}\n")
        f.write("\n")

        ## Runtime
        f.write("\truntime {\n")
        for runtime_key, runtime_value in doc_task.runtime.items():
            f.write(f"\t\t{runtime_key}: {runtime_value}\n")
        f.write("\t}\n")

        f.write("}\n")
        f.write("\n")
