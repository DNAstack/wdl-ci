# WDL Testing CLI

Tools to validate and test WDL-based repositories. To be used as part of CI/CD pipelines.

requires: python3.9+

install: `python -m pip install .`

run: `wdl-ci`

build docker image: `docker build -t wdl-testing-cli:latest .`

run docker container: `docker run wdl-testing-cli:latest`

run docker container (mount repo directory): `docker run -v ${PWD}:/usr/test wdl-testing-cli:latest`


# The wdl-ci config file

This file is created in the repos where wdl-ci is installed, i.e. the repos that host workflow files.


## Generating and updating the config file

`wdl-ci generate-config`

This will search through the pwd for all files with ".wdl" extensions and initialize the wdl-ci configuration file (`wdl-ci.config.json`). Tests and engines may then be configured by the user. The `workflow.task.digest` field should not be altered by the user; this field is used to detect task changes and rerun tests where necessary.

By default, only new workflows and/or tasks will be added to the config file; deleted workflows or tasks will not be removed. The `--remove` flag may be used to force removal of workflows and tasks that are no longer present at the specified paths.


## Config file structure

```json
{
  "workflows": {
    "<path/to/workflow.wdl>": {
      "key": "<path/to/workflow.wdl>",
      "name": "String",
      "description": "String",
      "tasks": {
        "<task_name>": {
          "key": "<task_name>",
          "digest": "String; autopopulated",
          "tests": [
            {
              "inputs": {
                "<input_name>": "<input_value>; type depends on input type",
                ...
              },
              "output_tests": {
                "<output_name>": {
                  "value": "<output_value>; type depends on output type",
                  "test_tasks": [
                    "<test task WDL basename>"
                  ]
                }
              },
              "struct_imports": [
                "<path/to/imports/defining/structs.wdl>"
              ]
            }
          ]
        }
      }
    }
  },
  "engines": {
    "<engine_id>": {
      "key": "<engine_id>",
      "enabled": "Boolean",
      "name": "String; human-readable name for the engine"
    }
  },
  "test_params": {
    "global_params": {
      "<param_name>": "String"
    },
    "engine_params": {
      "<engine_id>": {
        "<param_name>": "String"
      }
    }
  }
}
```

### workflows.\<workflow>.tasks.\<task>.tests[].struct_imports

- Struct imports can include non-struct blocks; only structs will be imported
- Nested imports by imported struct files will **not** be auto-imported; they must be explicitly added to the array of `struct_imports`
- Structs will be added in the order they appear in the array; take care to order imports appropriately


### workflows.test_params

Test params can be used to avoid repeating paths and values for test inputs and outputs.

- Parameters defined here can be used in inputs and outputs for task tests in the format `${param_name}`; these will be replaced with the `<param_value>` for workflow submission
- Global params will replace values for all engines
- Engine params will replace values only when submitting to a particular engine; useful if for example input sets exist across multiple environments and are prefixed with different paths


# Custom workflow linters

Custom linters may be added to [src/wdlci/linters/custom_linters.py](src/wdlci/linters/custom_linters.py).


# Workflow-based tests

Tests are defined in the [src/wdlci/wdl_tests](src/wdlci/wdl_tests) directory.

- Tests are written in WDL
- Test files must be named `${test_name}.wdl`
- In the test WDL file, before the task declaration, add a short description of what the purpose of this test is and what input type is expected, e.g.:

```
version 1.0

# Compare strings
# Input type: String

task compare_string {
  ...
```

- Each test file should contain a single test task, named `${test_name}`
- Tests must specify two inputs:
  - `${input_type} current_run_output`
  - `${input_type} validated_output`
- The `current_run_output` and `validated_output` will be passed to the test task automatically; it is up to the test writer to implement the desired comparison


Tests can be selected and applied to input sets by including the `${test_name}` as part of the `workflows.${workflow}.tasks.${task}.tests.[],test_tasks` array. For example, to run the `compare` test, which compares various output types, the `test_tasks` section should be set to `["compare"]`. Additional test tasks may be added for the same input set by adding test names to the `test_tasks` array for that set of inputs.


# Development

## Linting with black

Install [black](https://github.com/psf/black), then run `git config core.hooksPath hooks/`.

`black` will be run on all python files as a pre-commit hook.
