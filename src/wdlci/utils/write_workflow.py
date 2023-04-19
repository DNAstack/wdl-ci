import WDL
import subprocess
from importlib.resources import files
from wdlci.exception.wdl_test_cli_exit_exception import WdlTestCliExitException


def _order_structs(struct_typedefs):
    """
    Order struct_typedefs such that structs that are dependencies of other structs are written first
    This is necessary if the workflow is run using Cromwell
    Args:
        struct_typedefs ([WDL.Env.Binding]): structs imported by the main workflow
    Returns:
        ([WDL.Env.Binding]): Ordered list of struct_typedefs, with dependent structs before the structs that require them
    """

    def _flatten_array(array_member):
        if type(array_member) is WDL.Type.Array:
            return _flatten_array(array_member.item_type)
        else:
            return array_member

    def _get_dependencies(members, dependencies):
        for member_name, member in members.items():
            if type(member) is WDL.Type.StructInstance:
                dependencies.append(member.type_name)
                dependencies = _get_dependencies(member.members, dependencies)
            elif type(member) is WDL.Type.Array:
                array_member = _flatten_array(member)
                if type(array_member) is WDL.Type.StructInstance:
                    dependencies.append(array_member.type_name)
                    dependencies = _get_dependencies(array_member.members, dependencies)

        return list(set(dependencies))

    struct_info = dict()
    all_structs = list()
    for struct_def in struct_typedefs:
        struct_name = struct_def._name
        struct_dependencies = _get_dependencies(struct_def._value.members, list())

        struct_info[struct_name] = {
            "def": struct_def,
            "dependencies": struct_dependencies,
        }
        all_structs.append(struct_name)

    # Reorder all_structs such that structs that are dependencies of other structs come earlier in the array
    for struct_name, struct in struct_info.items():
        struct_index = all_structs.index(struct_name)

        # Move dependencies to earlier in the array if they occur later than the struct that depends on them
        for dependency in struct["dependencies"]:
            dependency_index = all_structs.index(dependency)
            if dependency_index > struct_index:
                all_structs.insert(struct_index, all_structs.pop(dependency_index))

    ordered_struct_defs = [
        struct_info[struct_name]["def"] for struct_name in all_structs
    ]
    return ordered_struct_defs


def write_workflow(
    workflow_name, main_task, output_tests, output_file, struct_typedefs
):
    """
    Write a workflow out to a file
    Args:
        workflow_name (str): Name of the test workflow being generated (workflow entrypoint)
        main_task (WDL.Tree.Task): Task to be tested
        output_tests ({output_name: {"value": output_value, "tasks": ["task0", "task1", "task2"]}}):
            Array of validated outputs and the test tasks to apply to them.
            Test tasks should map to files in wdl_tests/${test_task}.wdl
        output_file (str): Path to file to write workflow to
        struct_typedefs ([WDL.Env.Binding]): structs imported by the main workflow; these will be available to the test task
    """
    wdl_version = main_task.effective_wdl_version

    main_task_output_types = {output.name: output.type for output in main_task.outputs}

    with open(output_file, "w") as f:
        f.write(f"version {wdl_version}\n\n")

        # Order structs based on struct member dependencies
        struct_defs_ordered = _order_structs(struct_typedefs)

        for struct_def in struct_defs_ordered:
            f.write(f"struct {struct_def.name} {{\n")
            for member_name, member_type in struct_def._value.members.items():
                f.write(f"\t{member_type} {member_name}\n")
            f.write("}\n\n")

        f.write(f"workflow {workflow_name} {{\n")

        ## Inputs
        f.write("\tinput " + "{\n")
        for task_input in main_task.inputs:
            f.write(f"\t\t{task_input}\n")
        f.write("\n")
        for output_key in output_tests:
            test_output_type = main_task_output_types[output_key]
            # If a task output is optional, write the validated input as required (remove '?' from type); if the validated
            # output was provided, it means we expect an output from the task as well
            f.write(
                f"\t\t{str(test_output_type).replace('?', '')} TEST_OUTPUT_{output_key}\n"
            )
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
            output_type = str(main_task_output_types[output_key])
            scatter_indent = ""
            scatter_index = ""
            if output_type.startswith("Array"):
                f.write(
                    f"\tscatter (index in range(length(TEST_OUTPUT_{output_key}))) {{\n"
                )
                scatter_indent = "\t"
                scatter_index = "[index]"

            for test_task in output_value["test_tasks"]:
                test_task_key = f"{test_task}_{output_key}"

                test_wdl = files("wdlci.wdl_tests").joinpath(f"{test_task}.wdl")
                # Ensure that the test task WDL is valid
                try:
                    test_doc = WDL.load(str(test_wdl))
                    test_task_doc = test_doc.tasks[0]
                except:
                    subprocess.run(["miniwdl", "check", str(test_wdl)])
                    raise WdlTestCliExitException(f"Invalid test task [{test_wdl}]", 1)
                test_tasks[test_task_key] = test_task_doc

                f.write(
                    f"{scatter_indent}\tcall {test_task_doc.name} as {test_task_key} {{\n"
                )
                f.write(f"{scatter_indent}\t\tinput:\n")
                # If the current run output is an optional, coerce it into non-optional; we expect there to be an output if we have a test for it
                if output_type.endswith("?"):
                    f.write(
                        f"{scatter_indent}\t\t\tcurrent_run_output = select_first([{main_task.name}.{output_key}]){scatter_index},\n"
                    )
                else:
                    f.write(
                        f"{scatter_indent}\t\t\tcurrent_run_output = {main_task.name}.{output_key}{scatter_index},\n"
                    )
                f.write(
                    f"{scatter_indent}\t\t\tvalidated_output = TEST_OUTPUT_{output_key}{scatter_index}\n"
                )
                f.write(f"{scatter_indent}\t}}\n")

            if output_type.startswith("Array"):
                f.write("\t}\n")

        ## Outputs
        f.write("\n\toutput {\n")
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
        subprocess.run(["miniwdl", "check", output_file], check=True)
    except subprocess.CalledProcessError:
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
