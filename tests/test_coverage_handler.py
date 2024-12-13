import unittest
import os
import subprocess
import json
import warnings

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
        }

        call freebayes {
          input:
            bam=bam,
            ref=ref
        }

        output {
          File vcf = freebayes.vcf
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
"""

    def setUp(self):
        # Suppress the ResourceWarning complaining about the config_file json.load not being closed
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

    def update_config_with_tests(self, wdl_1_tests, wdl_2_tests):
        # Read the existing config file
        with open("wdl-ci.config.json", "r") as f:
            config = json.load(f)

        config["workflows"]["test_call-variants_1.wdl"]["tasks"]["freebayes"][
            "tests"
        ] = wdl_1_tests
        config["workflows"]["test_call-variants_2.wdl"]["tasks"]["freebayes"][
            "tests"
        ] = wdl_2_tests

        # Write the updated config back to the file
        with open("wdl-ci.config.json", "w") as f:
            json.dump(config, f, indent=2)

    def reset_coverage_summary(self):
        coverage_summary["untested_workflows"] = []
        coverage_summary["untested_tasks"] = {}
        coverage_summary["untested_outputs"] = {}
        coverage_summary["untested_outputs_with_optional_inputs"] = {}
        coverage_summary["tested_outputs_dict"] = {}
        coverage_summary["total_output_count"] = 0
        coverage_summary["all_tests_list"] = []
        coverage_summary["skipped_workflows"] = []

    def test_identical_output_names(self):
        # Reset the coverage_summary
        self.reset_coverage_summary()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ResourceWarning)

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
                wdl_1_tests=test_cases, wdl_2_tests=test_cases
            )

            # Call the coverage_handler function
            kwargs = {"target_coverage": None, "workflow_name": None}
            coverage_handler(kwargs)

            # Assert both workflows are not in the untested workflows list
            self.assertNotIn(
                "call_variants_1", coverage_summary["untested_workflows_list"]
            )
            self.assertNotIn(
                "call_variants_2", coverage_summary["untested_workflows_list"]
            )
            # Assert that the corresponding task is not in the untested tasks dictionary
            self.assertNotIn("freebayes", coverage_summary["untested_tasks_dict"])
            # Assert that "vcf" is found in both sets of {workflow: {task: [tested_outputs]}} in the parent untested_outputs_with_optional_inputs_dict
            self.assertIn(
                "vcf",
                coverage_summary["untested_outputs_with_optional_inputs_dict"][
                    "call_variants_1"
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

    # def test_no_tasks_in_workflow(self):
    #     self.reset_coverage_summary()
    #     # Suppress the ResourceWarning complaining about the config_file json.load not being closed
    #     with warnings.catch_warnings():
    #         warnings.simplefilter("ignore", ResourceWarning)
    #         # Update the "tests" list for specific workflows
    #         test_cases = []
    #         self.update_config_with_tests(
    #             wdl_1_tests=test_cases, wdl_2_tests=test_cases
    #         )
    #         # Call the coverage_handler function
    #         kwargs = {
    #             "target_coverage": None,
    #             "workflow_name": None,
    #         }
    #         coverage_handler(kwargs)
    #         # Assertions
    #         self.assertNotEqual(len(coverage_summary["untested_outputs_dict"]), 0)
    #         self.assertEqual(
    #             len(coverage_summary["untested_outputs_with_optional_inputs_dict"]), 2
    #         )
    #         self.assertEqual(len(coverage_summary["untested_tasks_dict"]), 2)

    #### Additional tests I'd like to add ####
    # Test workflows with >1 tasks
    # Test WDL files with >1 tasks but no 'workflow' block
    # Providing a value to command to --target-coverage where all outputs/tasks/workflows are above the thresold
    # Providing a value to --target-coverage where only some outputs/tasks/workflows are above the threshold
    # Providing a value to --target-coverage where none of the above are above the threshold
    # Providing any valid workflow name to --workflow-name
    # Providing an invalid workflow name to --workflow-name
    # Providing a valid workflow name to --workflow name where the workflow exists, but has no tasks
    # Providing an extremely large wdl-ci.config.json


if __name__ == "__main__":
    unittest.main()