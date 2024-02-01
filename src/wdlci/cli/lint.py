import json
import sys
import WDL
import WDL.Lint
import subprocess
from wdlci.config import Config
from wdlci.exception.wdl_test_cli_exit_exception import WdlTestCliExitException

# import wdlci.linters.custom_linters


def lint_handler(kwargs):
    suppress_lint_errors = kwargs["suppress_lint_errors"]
    print(f"Suppress lint errors: {suppress_lint_errors}")

    try:
        Config.load(kwargs)
        config = Config.instance()

        lint_failed_workflows = []

        for workflow_key in config.file.workflows.keys():
            # Pretty-print lint messages
            try:
                subprocess.run(["miniwdl", "check", workflow_key], check=True)
            except subprocess.CalledProcessError:
                raise WdlTestCliExitException(
                    f"Linting failed for workflow {workflow_key}", 1
                )

            lint = WDL.Lint.collect(WDL.Lint.lint(WDL.load(workflow_key)))
            num_unsuppressed_lints = len(
                [
                    pos
                    for (pos, lint_class, message, suppressed) in lint
                    if not suppressed
                ]
            )
            if num_unsuppressed_lints > 0:
                lint_failed_workflows.append(
                    {
                        "workflow": workflow_key,
                        "num_unsuppressed_lints": num_unsuppressed_lints,
                    }
                )
            print()

        if len(lint_failed_workflows) > 0:
            if suppress_lint_errors:
                print(f"[WARN] Suppressing lint errors in {lint_failed_workflows}")
            else:
                raise WdlTestCliExitException(
                    f"Unsuppressed warnings or errors in workflows {lint_failed_workflows}",
                    1,
                )

    except WdlTestCliExitException as e:
        print(f"exiting with code {e.exit_code}, message: {e.message}")
        sys.exit(e.exit_code)
