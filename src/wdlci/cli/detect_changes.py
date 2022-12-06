import jsonpickle
from wdltest.constants import CHANGES_JSON
from wdltest.model.changeset import Changeset

def detect_changes_handler():
    changeset = Changeset()
    workflow_change = changeset.add_workflow_change("workflows/main.wdl")
    workflow_change.add_task_change("align")

    encoded = jsonpickle.encode(changeset)
    open(CHANGES_JSON, "w").write(encoded)
