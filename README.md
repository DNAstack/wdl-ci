# WDL Testing CLI

**Note that this tool is not intended to access or manipulate protected health information (PHI). `wdl-ci` and its corresponding GitHub action should _not_ be configured with a workflow engine that has access to PHI, and PHI should not be used in tests.**

`wdl-ci` provides tools to validate and test workflows and tasks written in [Workflow Description Language (WDL)](https://github.com/openwdl/wdl). `wdl-ci` detects changes to workflow tasks and runs tests via [DNAstack's Workbench](https://docs.dnastack.com/docs/introduction-to-workbench) to confirm that the task still produces expected outputs.

When installed as a github action, `wdl-ci` will run the following steps:
1. Lint workflows
2. Detect tasks that have changed
3. If test inputs/outputs are defined for a changed task, submit a test workflow for each changed task
4. For successful tests, update task digests in the configuration file. Task digests are used to detect changes to tasks; a digest represents the last state of a task where all tests passed.

If any step of the action fails, the check will fail; however if some task tests succeed, the digests for those tasks will still be updated such that only failing tests will be rerun upon subsequent pushes.

# GitHub action usage

```yaml
- uses: dnastack/wdl-ci@v1.0.0
  with:
    # Configuration file where tests can be found
    # Default: wdl-ci.config.json
    config_file: ''

    # DNAstack wallet URL to authenticate with
    # WALLET_URL must be defined in actions secrets
    wallet-url: ${{ secrets.WALLET_URL }}

    # DNAstack wallet client ID
    # WALLET_CLIENT_ID must be defined in actions secrets
    wallet-client-id: ${{ secrets.WALLET_CLIENT_ID }}

    # DNAstack wallet client secret
    # WALLET_CLIENT_SECRET must be defined in actions secrets
    wallet-client-secret: ${{ secrets.WALLET_CLIENT_SECRET }}

    # DNAstack Workbench namespace. This determines which user's Workbench will be
    # responsible for workflow runs. Engines configured in the config-file must be
    # configured in this user's namespace.
    # WORKBENCH_NAMESPACE must be defined in actions secrets
    workbench-namespace: ${{ secrets.WORKBENCH_NAMESPACE }}

    # DNAstack Workbench EWES (Extended WES) URL
    # WORKBENCH_EWES_URL must be defined in actions secrets
    workbench-ewes-url: ${{ secrets.WORKBENCH_EWES_URL }}

    # DNAstack Workbench workflow service URL
    # WORKBENCH_WORKFLOW_SERVICE_URL must be defined in actions secrets
    workbench-workflow-service-url:  ${{ secrets.WORKBENCH_WORKFLOW_SERVICE_URL }}

    # DNAstack Workbench EWES refresh token
    # WORKBENCH_EWES_REFRESH_TOKEN must be defined in actions secrets
    workbench-ewes-refresh-token: ${{ secrets.WORKBENCH_EWES_REFRESH_TOKEN }}

    # DNAstack Workbench workflow service refresh token
    # WORKBENHC_WORKFLOW_SERVICE_REFRESH_TOKEN must be defined in actions secrets
    workbench-workflow-service-refresh-token: ${{ secrets.WORKBENCH_WORKFLOW_SERVICE_REFRESH_TOKEN }}

    # Directory containing custom test WDLs. If defined, this directory will be searched for
    # WDL test files specified as tests in the config-file prior to searching through tests
    # defined in src/wdlci/wdl_tests
    wdl_ci_custom_test_wdl_dir: ''
```

# Scenarios

- [Run on push to non-main/master branches](#run-on-push-to-non-mainmaster-branches)
- [Run on pull request](#run-on-pull-request)
- [Extend the tests available to wdl-ci](#extend-the-tests-available-to-wdl-ci)

## Run on push to non-main/master branches

```yaml
name: Lint and test workflows
on:
  push:
    branches:
      - '*'
      - '!master'
      - '!main'
jobs:
  wdl-ci:
    runs-on: ubuntu-latest
    steps:
      - name: checkout
        uses: actions/checkout@v3
        with:
          submodules: true
      - name: wdl-ci
        uses: dnastack/wdl-ci@v1.0.0
        with:
          wallet-url: ${{ secrets.WALLET_URL }}
          wallet-client-id: ${{ secrets.WALLET_CLIENT_ID }}
          wallet-client-secret: ${{ secrets.WALLET_CLIENT_SECRET }}
          workbench-namespace: ${{ secrets.WORKBENCH_NAMESPACE }}
          workbench-ewes-url: ${{ secrets.WORKBENCH_EWES_URL }}
          workbench-workflow-service-url:  ${{ secrets.WORKBENCH_WORKFLOW_SERVICE_URL }}
          workbench-ewes-refresh-token: ${{ secrets.WORKBENCH_EWES_REFRESH_TOKEN }}
          workbench-workflow-service-refresh-token: ${{ secrets.WORKBENCH_WORKFLOW_SERVICE_REFRESH_TOKEN }}
```

## Run on pull request

```yaml
name: Lint and test workflows
on: pull_request
jobs:
  wdl-ci:
    runs-on: ubuntu-latest
    steps:
      - name: checkout
        uses: actions/checkout@v3
        with:
          submodules: true
          repository: ${{ github.event.pull_request.head.repo.full_name }}
          ref: ${{ github.event.pull_request.head.ref }}
      - name: wdl-ci
        uses: dnastack/wdl-ci@v1.0.0
        with:
          wallet-url: ${{ secrets.WALLET_URL }}
          wallet-client-id: ${{ secrets.WALLET_CLIENT_ID }}
          wallet-client-secret: ${{ secrets.WALLET_CLIENT_SECRET }}
          workbench-namespace: ${{ secrets.WORKBENCH_NAMESPACE }}
          workbench-ewes-url: ${{ secrets.WORKBENCH_EWES_URL }}
          workbench-workflow-service-url:  ${{ secrets.WORKBENCH_WORKFLOW_SERVICE_URL }}
          workbench-ewes-refresh-token: ${{ secrets.WORKBENCH_EWES_REFRESH_TOKEN }}
          workbench-workflow-service-refresh-token: ${{ secrets.WORKBENCH_WORKFLOW_SERVICE_REFRESH_TOKEN }}
```

## Extend the tests available to wdl-ci

Define the `wdl_ci_custom_test_wdl_dir` to specify a directory containing custom WDL-based tests; these test tasks may then be used to test workflow tasks. See [WDL-based tests](#wdl-based-tests) for more information on writing custom test tasks. The `wdl_ci_custom_test_wdl_dir` should refer to a directory that exists in the target repository.

```yaml
name: Lint and test workflows
on: pull_request
jobs:
  wdl-ci:
    runs-on: ubuntu-latest
    steps:
      - name: checkout
        uses: actions/checkout@v3
        with:
          submodules: true
          repository: ${{ github.event.pull_request.head.repo.full_name }}
          ref: ${{ github.event.pull_request.head.ref }}
      - name: wdl-ci
        uses: dnastack/wdl-ci@v1.0.0
        with:
          wallet-url: ${{ secrets.WALLET_URL }}
          wallet-client-id: ${{ secrets.WALLET_CLIENT_ID }}
          wallet-client-secret: ${{ secrets.WALLET_CLIENT_SECRET }}
          workbench-namespace: ${{ secrets.WORKBENCH_NAMESPACE }}
          workbench-ewes-url: ${{ secrets.WORKBENCH_EWES_URL }}
          workbench-workflow-service-url:  ${{ secrets.WORKBENCH_WORKFLOW_SERVICE_URL }}
          workbench-ewes-refresh-token: ${{ secrets.WORKBENCH_EWES_REFRESH_TOKEN }}
          workbench-workflow-service-refresh-token: ${{ secrets.WORKBENCH_WORKFLOW_SERVICE_REFRESH_TOKEN }}
          wdl_ci_custom_test_wdl_dir: my-custom-test-dir
```

# Configuring and installing the GitHub action

1. Define secrets on the target repository.

The following secrets must be defined on the target repo (see [creating GitHub secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets#creating-encrypted-secrets-for-a-repository)):

- `WALLET_URL`
- `WALLET_CLIENT_ID`
- `WALLET_CLIENT_SECRET`
- `WORKBENCH_NAMESPACE`
- `WORKBENCH_EWES_URL`
- `WORKBENCH_WORKFLOW_SERVICE_URL`
- `WORKBENCH_EWES_REFRESH_TOKEN`
- `WORKBENCH_WORKFLOW_SERVICE_REFRESH_TOKEN`

2. Add the workflow.

Create a `workflow.yml` file in the target repo at the path `.github/workflows/workflow.yml`.

See [scenarios](#scenarios) for example workflow definitions.

3. [Generate a config file](#generating-and-updating-the-config-file).

4. Fill out tests and engines sections of [the config file](#config-file-structure).

5. Trigger the action.

Depending on the workflow you have configured, push to a non-main/master branch or open a pull request. Test runs will be triggered for any tasks that have altered digests (when initially adding the config file, this will be all tests, since their digests will be initialized to `""`) and that have tests defined. Test run status can be monitored on [Workbench](https://workbench.dnastack.com).


# The wdl-ci config file

The configuration file is named `wdl-ci.config.json` and should be created at the root of the repo where wdl-ci is installed, i.e. the repo that hosts workflow files to be tested.

## Generating and updating the config file

Generate a config file: `wdl-ci generate-config` (using Docker: `docker run -v ${PWD}:/usr/test dnastack/wdl-ci:latest generate-config`).

This will search through the present working directory for all files with ".wdl" extensions and initialize the wdl-ci configuration file (`wdl-ci.config.json`). Tests and engines may then be configured by the user. The `workflow.task.digest` field should not be altered by the user; this field is used to detect task changes and rerun tests where necessary.

## Config file structure

```json
{
  "workflows": {
    "<path/to/workflow.wdl>": {
      "key": "<path/to/workflow.wdl>; autopopulated",
      "tasks": {
        "<task_name>": {
          "key": "<task_name>; autopopulated",
          "digest": "<task_digest>; autopopulated",
          "tests": [
            {
              "inputs": {
                "<input_name>": "<input_value>"
              },
              "output_tests": {
                "<output_name>": {
                  "value": "<output_value>",
                  "test_tasks": [
                    "array of tests to apply to the task"
                  ]
                }
              }
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
      "name": "Human-readable name for the engine (optional)"
    }
  },
  "test_params": {
    "global_params": {
      "<param_name>": "<param_value>"
    },
    "engine_params": {
      "<engine_id>": {
        "<param_name>": "<param_value>"
      }
    }
  }
}
```

### `workflows`

The set of workflow files found in the repo.

- `key`: The path to the workflow relative to the wdl-ci.config.json file.
- `tasks`: An array of the tasks defined in the given workflow file

### `task`

- `key`: The task name
- `digest`: Autopopulated; a digest of the contents of the task. Used to determine whether a task has changed and tests should be run. To force a rerun of tests for a task, the digest can be set to the empty string.
- `tests`: Sets of validated inputs and outputs to use to run tests on the given task

### `tests`

An array of different input sets and their corresponding validated outupts. Each input/output set can have a different set of tests applied to them; this may be useful if for example you want to ensure your task works across several different sample sets.

#### `inputs`

Inputs required by the task to be tested. Must define all required inputs to the task. Input values can use parameters defined in [test_params](#test_params).

If an input is a file, the value should be the path to the file on the filesystem corresponding to the engine(s) that have been configured in the [engines section](#engines). This must be a file that is accessible by the engine.

#### `output_tests`

Outputs from the task to be tested. Not all outputs must be defined or tested. This field is an object containing one entry per output to be tested, where the object key is the name of the output and the value is an object with keys:

- `value`: Validated output of the task from a previous run.
- `test_tasks`: This specifies the array of tests that should be applied to a specific output. See [WDL-based tests](#WDL-based-tests) for information on defining and using test tasks on outputs.


```json
"output_tests": {
  "<output_name>": {
    "value": "<output_value>",
    "test_tasks": []
  }
}
```

Each test task will be passed the validated output as well as the output from the current test run of the task, and they will be compared as defined in the test task WDL.

Output values can use parameters defined in [test_params](#test_params).

### `engines`

**Do not configure an engine that has access to protected health information, even if that data is not being used in tests.** Ideally a workflow engine that is used only for testing and has access only to non-protected test input files should be used.

Engines configured in Workbench that test tasks will be submitted to. The engine ID can be found in the engine configuration on Workbench.
- `key`: The engine ID, found from the engine configuration on Workbench
- `enabled`: `true` to enable submitting tasks to the workflow; `false` otherwise
- `name`: Optional human-readable name for the engine; used to distinguish configured engines

Multiple engines can be configured. Tests will be submitted to all enabled engines; if two engines are enabled, each test will run in each engine.

### `test_params`

Test params can be used to avoid repeating paths and values for test inputs and outputs.

- Parameters defined here can be used in inputs and outputs for task tests in the format `${param_name}`; these will be replaced with the `<param_value>` for workflow submission
- Global params will replace values for all engines
- Engine params will replace values only when submitting to a particular engine; useful if for example input sets exist across multiple environments and are prefixed with different paths
- Objects and arrays can be used for parameters; if you are using a complex parameter as an input or output value, this parameter must be the only content of the value, e.g. `"my_input": "${complex_param}"`, not `"my_input": "${complex_param}.some_key"`
- Complex parameters can themselves use parameters, and will be substituted appropriately

```json
"test_params": {
  "global_params": {
    "reference_name": "MN12345"
    "reference_fasta": {
      "data": "${base_path}/${reference_name}.fa",
      "data_index": "${base_path}/${reference_name}.fa.fai"
    },
    "bwa_files": {
      "reference_fasta": "${reference_fasta}",
      "reference_ann": "${base_path}/${reference_name}.ann",
      "reference_pac": "${base_path}/${reference_name}.pac"
    }
  },
  "engine_params": {
    "engine_A": {
      "base_path": "/data"
    },
    "engine_B": {
      "base_path": "/home/admin/pipeline_files"
    }
  }
}
```

# WDL-based tests

Tests are defined in the [src/wdlci/wdl_tests](src/wdlci/wdl_tests) directory.

- Tests are written in WDL
- Test files must be named `<test_name>.wdl`
- In the test WDL file, before the task declaration, add a short description of what the purpose of this test is and what input type is expected, e.g.:

```wdl
version 1.0

# Compare strings
# Input type: String

task compare_string {
  input {
    String current_run_output
    String validated_output
  }
  ...
```

- Each test file should contain a single test task, named `<test_name>`
- Tests must specify two inputs:
  - `<input_type> current_run_output`
  - `<input_type> validated_output`
- The `current_run_output` and `validated_output` will be passed to the test task automatically; it is up to the test writer to implement the desired comparison


Tests can be selected and applied to task outputs by including the `<test_name>` as part of the `test_tasks` array in [the output tests block](#output_tests). For example, to run the `compare_string` test, the `test_tasks` section for the output to be tested should be set to `["compare_string"]`.

## Array comparison

If an output is of type `Array[X]`, the test task will be automatically scattered over the outputs, and any tests will be run once for each item in the validated output array. Validated outputs must be present in the same order as the outputs from the task. Due to the scatter over elements of array-type outputs, both array-type and non-array-type outputs should use the same underlying tests which operate on items of type `X`.

It is not necessary to test every item in the current run output array, but keep in mind that if a subset of the outputs are to be tested, they must be the first items in the output array. All items in the validated output array will be compared to the items in the corresponding current run output array at the same array index.

## Custom tests

Custom test WDLs may be defined in a directory located in the target repository. To allow `wdl-ci` access to custom tests, the `WDL_CI_CUSTOM_TEST_WDL_DIR` environment variable must be set (GitHub action: [run with `wdl_ci_custom_test_wdl_dir` set](#extend-the-tests-available-to-wdl-ci)).


# Local installation

`wdl-ci` is meant to be run as part of a GitHub action, but can be installed locally for testing and linting.

The following environment variables must be defined when running `wdl-ci`:

- `WALLET_URL`
- `WALLET_CLIENT_ID`
- `WALLET_CLIENT_SECRET`
- `WORKBENCH_NAMESPACE`
- `WORKBENCH_EWES_URL`
- `WORKBENCH_WORKFLOW_SERVICE_URL`
- `WORKBENCH_EWES_REFRESH_TOKEN`
- `WORKBENCH_WORKFLOW_SERVICE_REFRESH_TOKEN`

Optionally, the `WDL_CI_CUSTOM_TEST_WDL_DIR` environment variable may used to specify an additional directory where WDL-based tests may be found.

## Installing using pip

Requires: python3.9+

Installation: `python3 -m pip install .`

Run: `wdl-ci`

## Running using Docker

A Docker image is available from [DNAstack's dockerhub](https://hub.docker.com/r/dnastack/wdl-ci) as `dnastack/wdl-ci`.

Run `wdl-ci` via the Docker container: `docker run dnastack/wdl-ci:latest`

Run `wdl-ci` via the Docker container (mounting the target repository, run from the root of the target repository): `docker run -v ${PWD}:/usr/test dnastack/wdl-ci:latest`

Commands and arguments to wdl-ci can be passed after the run command, e.g. `docker run -v ${PWD}:/usr/test dnastack/wdl-ci:latest lint`.

To pass required environment variables, they may be written to a newline-delimited file in the format `WALLET_URL=value` and passed to the `docker run` command using the `--env-file <env_file>` argument.

Run a wdl-ci command, using variables defined in `wdl-ci.env`: `docker run --env-file wdl-ci.env -v ${PWD}:/usr/test dnastack/wdl-ci:latest submit`


# Commands

## Generate a config file

Generates the configuration file that is required by other commands. See [here](#the-wdl-ci-config-file) for information about its structure. This command will recursively search through your present working directory for files ending in .wdl, and will initialize a configuration file with these workflows and their tasks filled out.

If a configuration file already exists, this will add workflows or tasks that do not already exist in the file. By default, only new workflows and/or tasks will be added to the config file; deleted workflows or tasks will not be removed. The `--remove` flag may be used to force removal of workflows and tasks that are no longer present at the specified paths.

`wdl-ci generate-config [--remove]`

## Lint workflows

`wdl-ci lint`

## Detect changed tasks

`wdl-ci detect-changes`

## Submit test runs

This should be run following `wdl-ci detect-changes` to submit tests for tasks that have changes and that have tests defined.

`wdl-ci submit`

## Monitor running tests

This should be run following `wdl-ci submit` to monitor the status of running tests. Workflow status is polled every 60 seconds until all workflows have completed.

`wdl-ci monitor`

## Clean up custom workflows from the Workbench namespace

Note that this will remove _all_ custom workflows from your namespace; use with caution.

`wdl-ci cleanup`


# Development

## Linting with black

Install [black](https://github.com/psf/black), then run `git config core.hooksPath hooks/`.

`black` will be run on all python files as a pre-commit hook.
