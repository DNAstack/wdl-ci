import json
import sys
import WDL
import WDL.Lint
from WDL.Lint import a_linter, Linter
from WDL.CLI import check
from wdlci.config import Config
from typing import Any
from wdlci.exception.wdl_test_cli_exit_exception import WdlTestCliExitException


@a_linter
class MissingRuntimeKey(Linter):
    required_keys = set(
        [
            "docker",
            "cpu",
            "memory",
            "disk",
            "disks",
            "preemptible",
            "maxRetries",
            "awsBatchRetryAttempts",
            "queueArn",
            "zones",
        ]
    )

    def task(self, obj: WDL.Tree.Task) -> Any:
        for k in self.required_keys:
            if k not in obj.runtime:
                self.add(obj, "Missing required runtime parameter: " + k)


def lint_handler(kwargs):

    try:
        Config.load(kwargs)
        config = Config.instance()

        lint_failed_workflows = []

        for workflow_key in config.file.workflows.keys():
            # Pretty-print lint messages
            WDL.CLI.check([workflow_key])

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
            raise WdlTestCliExitException(
                f"Unsuppressed warnings or errors in workflows {lint_failed_workflows}",
                1,
            )

    except WdlTestCliExitException as e:
        print(f"exiting with code {e.exit_code}, message: {e.message}")
        sys.exit(e.exit_code)
