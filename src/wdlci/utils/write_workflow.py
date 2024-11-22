import WDL
import subprocess
from pathlib import Path
from importlib.resources import files
from wdlci.exception.wdl_test_cli_exit_exception import WdlTestCliExitException
from wdlci.config.config_file import WorkflowTaskConfig, WorkflowTaskTestConfig
import linecache


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


def _get_output_type(main_task_output_types, output_key):
    if output_key in main_task_output_types:
        return main_task_output_types[output_key]
    # output is a struct
    else:
        main_output_key = output_key.split(".")[0]
        sub_output_key = ".".join(output_key.split(".")[1:])
        struct_def = main_task_output_types[main_output_key]
        struct_member_types = struct_def.members
        return _get_output_type(struct_member_types, sub_output_key)


def write_workflow(
    workflow_name,
    main_doc,
    main_task,
    output_tests,
    output_file,
    struct_typedefs,
    custom_test_dir=None,
):
    """
    Write a workflow out to a file
    Args:
        workflow_name (str): Name of the test workflow being generated (workflow entrypoint)
        main_doc (WDL.Tree.Document): Document from which the main task originated
        main_task (WDL.Tree.Task): Task to be tested
        output_tests ({output_name: {"value": output_value, "tasks": ["task0", "task1", "task2"]}}):
            Array of validated outputs and the test tasks to apply to them.
            Test tasks should map to files in wdl_tests/${test_task}.wdl
        output_file (str): Path to file to write workflow to
        struct_typedefs ([WDL.Env.Binding]): structs imported by the main workflow; these will be available to the test task
        custom_test_dir (str): Path to a directory containing test WDL tasks; this directory will be checked for test tasks first
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
            test_output_type = _get_output_type(main_task_output_types, output_key)

            # If a task output is optional, write the validated input as required (remove '?' from type); if the validated
            # output was provided, it means we expect an output from the task as well
            f.write(
                f"\t\t{str(test_output_type).replace('?', '')} TEST_OUTPUT_{output_key.replace('.', '_')}\n"
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
            output_type = str(_get_output_type(main_task_output_types, output_key))
            scatter_indent = ""
            scatter_index = ""
            if output_type.startswith("Array"):
                f.write(
                    f"\tscatter (index in range(length(TEST_OUTPUT_{output_key.replace('.', '_')}))) {{\n"
                )
                scatter_indent = "\t"
                scatter_index = "[index]"

            for test_task in output_value["test_tasks"]:
                test_task_key = f"{test_task}_{output_key.replace('.', '_')}"

                # Try to find a user-defined test wdl
                test_wdl = None
                if custom_test_dir is not None:
                    test_wdl = Path(f"{custom_test_dir}/{test_task}.wdl")

                # If a user-defined test WDL does not exist, try to find the test in wdl_tests
                if test_wdl is None or not test_wdl.exists():
                    test_wdl = files("wdlci.wdl_tests").joinpath(f"{test_task}.wdl")

                # Ensure that the test task WDL is valid
                try:
                    test_doc = WDL.load(str(test_wdl))
                    test_task_doc = test_doc.tasks[0]
                except:
                    subprocess.run(["miniwdl", "check", str(test_wdl)])
                    raise WdlTestCliExitException(f"Invalid test task [{test_wdl}]", 1)
                test_tasks[test_task_key] = {"task": test_task_doc, "doc": test_doc}

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
                    f"{scatter_indent}\t\t\tvalidated_output = TEST_OUTPUT_{output_key.replace('.', '_')}{scatter_index}\n"
                )
                f.write(f"{scatter_indent}\t}}\n")

            if output_type.startswith("Array"):
                f.write("\t}\n")

        ## Outputs
        f.write("\n\toutput {\n")
        for test_task_key, task_info in test_tasks.items():
            for task_output in task_info["task"].outputs:
                f.write(
                    f"\t\t{task_output.type} {test_task_key}_{task_output.name} = {test_task_key}.{task_output.name}\n"
                )
        f.write("\t}\n")
        f.write("\n")

        f.write("}\n")
        f.write("\n")

    _write_task(main_doc, main_task, output_file)
    tasks_written = list()
    for task_info in test_tasks.values():
        test_doc = task_info["doc"]
        test_task = task_info["task"]
        if test_task.name not in tasks_written:
            _write_task(test_doc, test_task, output_file)
            tasks_written.append(test_task.name)

    # Ensure the workflow is valid
    try:
        subprocess.run(["miniwdl", "check", output_file], check=True)
    except subprocess.CalledProcessError:
        raise WdlTestCliExitException(
            f"Invalid test workflow [{output_file}] generated; exiting", 1
        )


def _write_task(doc, task, output_file):
    """
    Write a task out to a file
    Args:
        doc (WDL.Tree.Document): Document containing task to write
        task (WDL.Tree.Task): task to write
        output_file (str): Path to file to write task to
    """
    with open(output_file, "a") as f:
        f.write(f"task {task.name} {{\n")

        ## Inputs
        f.write("\tinput " + "{\n")
        for task_input in task.inputs:
            f.write(f"\t\t{task_input}\n")
        f.write("\t}\n")
        f.write("\n")

        ## Post inputs
        for post_input in task.postinputs:
            f.write(f"\t{post_input}\n")
        f.write("\n")

        ## Command
        f.write("\tcommand <<<\n")
        task_cmd_start = task.command.pos.line
        task_cmd_end = task.command.pos.end_line - 1
        for line in doc.source_lines[task_cmd_start:task_cmd_end]:
            f.write(f"{line}\n")
        f.write("\t>>>\n")
        f.write("\n")

        ## Outputs
        f.write("\toutput {\n")
        for task_output in task.outputs:
            f.write(f"\t\t{task_output}\n")
        f.write("\t}\n")
        f.write("\n")

        ## Runtime
        f.write("\truntime {\n")
        for runtime_key, runtime_value in task.runtime.items():
            f.write(f"\t\t{runtime_key}: {runtime_value}\n")
        f.write("\t}\n")

        f.write("}\n")
        f.write("\n")
