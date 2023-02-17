# WDL Testing CLI

Tools to validate and test WDL-based repositories. To be used as part of CI/CD pipelines.

requires: python3.9+

install: `python -m pip install .`

run: `wdl-ci`

build docker image: `docker build -t wdl-testing-cli:latest .`

run docker container: `docker run wdl-testing-cli:latest`

run docker container (mount repo directory): `docker run -v ${PWD}:/usr/test wdl-testing-cli:latest`


## Generating and updating the wdl-ci config file

`wdl-ci generate-config`

This will search through the pwd for all files with ".wdl" extensions and initialize the wdl-ci configuration file (`wdl-ci.config.json`). Tests and engines may then be configured by the user. The `workflow.task.digest` field should not be altered by the user; this field is used to detect task changes and rerun tests where necessary.

By default, only new workflows and/or tasks will be added to the config file; deleted workflows or tasks will not be removed. The `--remove` flag may be used to force removal of workflows and tasks that are no longer present at the specified paths.


## Custom workflow linters

Custom linters may be added to [src/wdlci/linters/custom_linters.py](src/wdlci/linters/custom_linters.py).


## Worklfow-based tests

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


## Linting with black

Install [black](https://github.com/psf/black), then run `git config core.hooksPath hooks/`.

`black` will be run on all python files as a pre-commit hook.
