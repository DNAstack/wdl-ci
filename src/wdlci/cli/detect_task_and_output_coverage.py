import sys
import WDL
from wdlci.config import Config
from wdlci.config.config_file import WorkflowTaskConfig, WorkflowTaskTestConfig
from wdlci.exception.wdl_test_cli_exit_exception import WdlTestCliExitException


def detect_task_and_output_coverage_handler(kwargs):
    try:
        Config.load(kwargs)
        config = Config.instance()

        tasks_without_tests = []
        outputs_without_tests = []

        task_coverage = {}
        output_coverage = {}

        for workflow, workflow_config in config.file.workflows.items():
            doc = WDL.load(workflow)

            for task in doc.tasks:
                task_name = task.name

                # task_test_configs is a list of WorkflowTaskTestConfig objects,
                # which contain inputs and output_tests as attributes
                task_test_configs = workflow_config.tasks[task_name].tests
                if not task_test_configs:
                    tasks_without_tests.append(task_name)

                task_coverage_count = 0

                for task_test_config in task_test_configs:
                    # Create a dictionary of output tests
                    output_tests_dict = task_test_config.output_tests
                    # Also created a nested dictionary of output coverage, which will
                    # store a task name as the parent key
                    output_coverage[task_name] = {}
                    # For each key and value in a given output test dict
                    for output_key, output_value in output_tests_dict.items():
                        # Ensure output value is a dict with the key test_tasks present
                        if (
                            isinstance(output_value, dict)
                            and "test_tasks" in output_value
                        ):
                            # Create a list of test tasks for each output
                            output_tests_list = output_value["test_tasks"]
                            # Assign the number of test tasks to the key associated with a
                            # given output in a nested structure, where each task has a
                            # dictionary of outputs and their task counts
                            output_coverage[task_name][output_key] = len(
                                output_tests_list
                            )
                            task_coverage_count += len(output_tests_list)

                            if len(output_tests_list) == 0:
                                outputs_without_tests.append(output_key)
                    task_coverage[task_name] = task_coverage_count

        print("Task Coverage:")
        for task_name, tests_count in task_coverage.items():
            print(f"\t{task_name}: {tests_count}\n")

        print("Output coverage:")
        for task_name, output_tests_dict in output_coverage.items():
            print(f"\tTask name: {task_name}")
            for output_name, tests_count in output_tests_dict.items():
                print(
                    f"\t\tOutput name: {output_name}\n\t\t\tnumber of tests: {tests_count}"
                )

        if tasks_without_tests and outputs_without_tests:
            print(
                f"\nWARNING: The following tasks have no tests:\n\n{', '.join(tasks_without_tests)}\n\n"
                + f"Additionally, the following outputs have no tests:\n\n{', '.join(outputs_without_tests)}\n\n"
            )
        elif tasks_without_tests:
            print(
                f"\nWARNING: The following tasks have no tests:\n\n{', '.join(tasks_without_tests)}\n\n"
            )
        elif outputs_without_tests:
            print(
                f"\nWARNING: The following outputs have no tests:\n\n{', '.join(outputs_without_tests)}\n\n"
            )

    except WdlTestCliExitException as e:
        print(f"exiting with code {e.exit_code}, message: {e.message}")
        sys.exit(e.exit_code)
