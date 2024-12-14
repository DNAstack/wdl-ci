import unittest
import os
import subprocess
import json
import warnings
import sys

from src.wdlci.cli.coverage import coverage_handler, coverage_summary


class TestCoverageHandler(unittest.TestCase):
    EXAMPLE_WDL_WORKFLOW = """
      version 1.0

      struct Reference {
        File fasta
        String organism
      }

      workflow call_variants {
        input {
          File bam
          Reference ref
          String input_str
        }

        call freebayes as freebayes_1 {
          input:
            bam=bam,
            ref=ref
        }

        call hello_world {
          input:
            input_str = input_str
        }

        output {
          File vcf = freebayes_1.vcf
          File greeting = hello_world.greeting
        }
      }

      task freebayes {
        input {
          File bam
          Reference ref
          Float? min_alternate_fraction
        }

        String prefix = basename(bam, ".bam")
        Float default_min_alternate_fraction = select_first([min_alternate_fraction, 0.2])

        command <<<
        freebayes -v '~{prefix}.vcf' -f ~{ref.fasta} \
          -F ~{default_min_alternate_fraction} \
          ~{bam}
        >>>

        runtime {
          docker: "quay.io/biocontainers/freebayes:1.3.2--py36hc088bd4_0"
        }

        output {
          File vcf = "${prefix}.vcf"
        }
      }

      task hello_world {
        input {
         String input_str
        }

        command <<<
          echo ~{input_str} > output_str.txt
        >>>

        runtime {
          docker: "ubuntu:xenial"
        }

        output {
          File greeting = "output_str.txt"
        }
      }
"""

    def setUp(self):
        # Redirect stdout to hide the output of the coverage command and just see the test results
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, "w")
        # Suppress the ResourceWarning complaining about the config_file json.load not being closed
        warnings.simplefilter("ignore", ResourceWarning)
        # Create the WDL files with different workflow names
        wdl_workflow_1 = self.EXAMPLE_WDL_WORKFLOW.replace(
            "call_variants", "call_variants_1"
        )
        wdl_workflow_2 = self.EXAMPLE_WDL_WORKFLOW.replace(
            "call_variants", "call_variants_2"
        )

        with open("test_call-variants_1.wdl", "w") as f:
            f.write(wdl_workflow_1)
        with open("test_call-variants_2.wdl", "w") as f:
            f.write(wdl_workflow_2)
        # Run the wdl-ci generate-config subcommand
        subprocess.run(
            ["wdl-ci", "generate-config"], check=True, stdout=subprocess.DEVNULL
        )

    def tearDown(self):
        # Remove the WDL files
        if os.path.exists("test_call-variants_1.wdl"):
            os.remove("test_call-variants_1.wdl")
        if os.path.exists("test_call-variants_2.wdl"):
            os.remove("test_call-variants_2.wdl")
        if os.path.exists("wdl-ci.config.json"):
            os.remove("wdl-ci.config.json")
        sys.stdout.close()
        sys.stdout = self._original_stdout
        self.reset_coverage_summary()

    def update_config_with_tests(self, workflow_name, task_name, wdl_tests):
        # Read the existing config file
        with open("wdl-ci.config.json", "r") as f:
            config = json.load(f)

        config["workflows"][workflow_name]["tasks"][task_name]["tests"] = wdl_tests

        # Write the updated config back to the file
        with open("wdl-ci.config.json", "w") as f:
            json.dump(config, f, indent=2)

    def reset_coverage_summary(self):
        coverage_summary["untested_workflows_list"] = []
        coverage_summary["untested_tasks_dict"] = {}
        coverage_summary["untested_outputs_dict"] = {}
        coverage_summary["untested_outputs_with_optional_inputs_dict"] = {}
        coverage_summary["tested_outputs_dict"] = {}
        coverage_summary["total_output_count"] = 0
        coverage_summary["all_outputs_list"] = []
        coverage_summary["skipped_workflows_list"] = []

    def test_identical_output_names_with_threshold(self):
        # Update the "tests" list for specific workflows
        test_cases = [
            {
                "inputs": {
                    "bam": "test.bam",
                    "ref": {"fasta": "test.fasta", "organism": "test_organism"},
                },
                "output_tests": {
                    "vcf": {
                        "value": "test.vcf",
                        "test_tasks": ["compare_file_basename"],
                    }
                },
            }
        ]
        self.update_config_with_tests(
            workflow_name="test_call-variants_1.wdl",
            task_name="freebayes",
            wdl_tests=test_cases,
        )
        self.update_config_with_tests(
            workflow_name="test_call-variants_2.wdl",
            task_name="freebayes",
            wdl_tests=test_cases,
        )

        # Call the coverage_handler function
        kwargs = {"target_coverage": 50, "workflow_name": None}
        coverage_handler(kwargs)

        # Assert both workflows are not in the untested workflows list
        self.assertNotIn("call_variants_1", coverage_summary["untested_workflows_list"])
        self.assertNotIn("call_variants_2", coverage_summary["untested_workflows_list"])
        # Assert that the corresponding task is not in the untested tasks dictionary
        self.assertNotIn("freebayes", coverage_summary["untested_tasks_dict"])
        # Assert that "vcf" is found in both sets of {workflow: {task: [tested_outputs]}} in the parent untested_outputs_with_optional_inputs_dict
        self.assertIn(
            "vcf",
            coverage_summary["untested_outputs_with_optional_inputs_dict"][
                "call_variants_1"
            ]["freebayes"],
        )
        self.assertIn(
            "vcf",
            coverage_summary["untested_outputs_with_optional_inputs_dict"][
                "call_variants_2"
            ]["freebayes"],
        )
        # Assert that "vcf" is found in both sets of {workflow: {task: [tested_outputs]}} in the parent tested_output_dict
        self.assertIn(
            "vcf",
            coverage_summary["tested_outputs_dict"]["call_variants_1"]["freebayes"],
        )
        self.assertIn(
            "vcf",
            coverage_summary["tested_outputs_dict"]["call_variants_2"]["freebayes"],
        )

    # Case where no tasks are tested at all
    def test_no_tasks_in_workflow(self):
        # Update the "tests" list for specific workflows
        test_cases = []
        self.update_config_with_tests(
            workflow_name="test_call-variants_1.wdl",
            task_name="freebayes",
            wdl_tests=test_cases,
        )
        self.update_config_with_tests(
            workflow_name="test_call-variants_2.wdl",
            task_name="freebayes",
            wdl_tests=test_cases,
        )
        # Call the coverage_handler function
        kwargs = {
            "target_coverage": None,
            "workflow_name": None,
        }
        coverage_handler(kwargs)

        # Assertions

        # Assert all four outputs are untested
        self.assertEqual(
            sum(
                len(tasks)
                for tasks in coverage_summary["untested_outputs_dict"].values()
            ),
            4,
        )

        # Assert both outputs with optional inputs are not dually tested
        self.assertEqual(
            sum(
                len(tasks)
                for tasks in coverage_summary[
                    "untested_outputs_with_optional_inputs_dict"
                ].values()
            ),
            2,
        )
        # Assert all four tasks are untested
        self.assertEqual(
            sum(
                len(tasks) for tasks in coverage_summary["untested_tasks_dict"].values()
            ),
            4,
        )
        # Assert both workflows are untested
        self.assertGreaterEqual(len(coverage_summary["untested_workflows_list"]), 2)

    # Providing a valid workflow name to --workflow name where the workflow exists, but has no tests
    def test_valid_workflow_name_with_no_tasks(self):
        test_cases = [
            # {
            #     "inputs": {"input_str": "hello_world"},
            #     "output_tests": {
            #         "greeting": {
            #             "value": "hello world",
            #             "test_tasks": ["compare_string"],
            #         }
            #     },
            # }
        ]
        # Update the workflow we are NOT filtering for
        self.update_config_with_tests(
            workflow_name="test_call-variants_1.wdl",
            task_name="hello_world",
            wdl_tests=test_cases,
        )
        kwargs = {"target_coverage": None, "workflow_name": "call_variants_2"}
        coverage_handler(kwargs)

        # Assertions

        # Assert one workflow is untested (in reality both are, but we are filtering for one)
        self.assertEqual(len(coverage_summary["untested_workflows_list"]), 1)

        # Assert both tasks in the workflow we are filtering for are untested
        self.assertEqual(
            sum(
                len(tasks) for tasks in coverage_summary["untested_tasks_dict"].values()
            ),
            2,
        )

    # Providing an invalid workflow name to --workflow-name
    ## TODO: this doesn't work as the config doesn't get reset when the workflow exits with the No workflows found method -- adjust config reset to support
    # def test_invalid_workflow_name(self):
    #     kwargs = {"target_coverage": None, "workflow_name": "nonexistent_workflow"}

    #     coverage_handler(kwargs)
    #     output = sys.stdout

    #     # Assert that the output contains the expected message
    #     expected_message = f"No workflows found matching the filter: [{kwargs['workflow_name']}] or the workflow you searched for has no tasks or workflow attribute"
    #     self.assertIn(expected_message, output)

    #### Additional tests I'd like to add ####
    # Test workflows with >1 tasks
    # Test WDL files with >1 tasks but no 'workflow' block
    # Providing a value to command to --target-coverage where all outputs/tasks/workflows are above the thresold
    # Providing a value to --target-coverage where only some outputs/tasks/workflows are above the threshold
    # Providing a value to --target-coverage where none of the above are above the threshold
    # Providing an extremely large wdl-ci.config.json
    # Case where some tasks with optional inputs have outputs dually tested but others do not


if __name__ == "__main__":
    unittest.main()
