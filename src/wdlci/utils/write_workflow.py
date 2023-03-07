import WDL
from importlib.resources import files
from wdlci.exception.wdl_test_cli_exit_exception import WdlTestCliExitException


def write_workflow(workflow_name, main_task, output_tests, output_file):
    """
    Write a workflow out to a file
    Args:
        workflow_name (str): Name of the workflow (workflow entrypoint)
        main_task (WDL.Tree.Task): Task to be tested
        output_tests ({output_name: {"value": output_value, "tasks": ["task0", "task1", "task2"]}}):
            Array of validated outputs and the test tasks to apply to them.
            Test tasks should map to files in wdl_tests/${test_task}.wdl
        output_file (str): Path to file to write workflow to
    """
    wdl_version = main_task.effective_wdl_version

    main_task_output_types = {output.name: output.type for output in main_task.outputs}

    with open(output_file, "w") as f:
        f.write(f"version {wdl_version}\n\n")

        f.write(f"workflow {workflow_name} {{\n")

        ## Inputs
        f.write("\tinput " + "{\n")
        for task_input in main_task.inputs:
            f.write(f"\t\t{task_input}\n")
        f.write("\n")
        for output_key in output_tests:
            test_output_type = main_task_output_types[output_key]
            f.write(f"\t\t{test_output_type} TEST_OUTPUT_{output_key}\n")
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

        ## Call to test tasks
        test_tasks = dict()
        for output_key, output_value in output_tests.items():
            for test_task in output_value["test_tasks"]:
                test_task_key = f"{test_task}_{output_key}"

                test_wdl = files("wdlci.wdl_tests").joinpath(f"{test_task}.wdl")
                # Ensure that the test task WDL is valid
                try:
                    test_doc = WDL.load(str(test_wdl))
                    test_task_doc = test_doc.tasks[0]
                except:
                    raise WdlTestCliExitException(f"Invalid test task [{test_wdl}]", 1)
                test_tasks[test_task_key] = test_task_doc

                f.write(f"\tcall {test_task_doc.name} as {test_task_key} {{\n")
                f.write("\t\tinput:\n")
                f.write(f"\t\t\tcurrent_run_output = {main_task.name}.{output_key},\n")
                f.write(f"\t\t\tvalidated_output = TEST_OUTPUT_{output_key}\n")
                f.write("\t}\n")

        ## Outputs
        f.write("\toutput {\n")
        for test_task_key, test_task_doc in test_tasks.items():
            for task_output in test_task_doc.outputs:
                f.write(
                    f"\t\t{task_output.type} {test_task_key}_{task_output.name} = {test_task_key}.{task_output.name}\n"
                )
        f.write("\t}\n")
        f.write("\n")

        f.write("}\n")
        f.write("\n")

    _write_task(main_task, output_file)
    tasks_written = list()
    for test_task_doc in test_tasks.values():
        if test_task_doc.name not in tasks_written:
            _write_task(test_task_doc, output_file)
            tasks_written.append(test_task_doc.name)

    # Ensure the workflow is valid
    try:
        wdl_doc = WDL.load(output_file)
    except:
        raise WdlTestCliExitException(
            f"Invalid test workflow [{output_file}] generated; exiting", 1
        )


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
