import WDL
from WDL.Lint import a_linter, Linter
from typing import Any


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
