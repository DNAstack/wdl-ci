from datetime import datetime


class SubmissionState(object):
    def __init__(self):
        self.workflows = {}
        self.engines = {}
        self.workflow_runs = []

    def add_workflow(self, workflow_key, workflow_id):
        self.workflows[workflow_key] = SubmissionStateWorkflow(
            workflow_key, workflow_id
        )

    def add_engine(self, engine_id, engine_json):
        self.engines[engine_id] = engine_json

    def add_workflow_run(
        self, workflow_key, workflow_id, task_key, test_i, engine_key, inputs, outputs
    ):
        workflow_run = SubmissionStateWorkflowRun(
            workflow_key, workflow_id, task_key, test_i, engine_key, inputs, outputs
        )
        self.workflow_runs.append(workflow_run)
        return workflow_run

    def submit_all(self):
        # TODO: implement dummy method
        for submission in self.submissions:
            submission.set_status_submitted()


class SubmissionStateWorkflow(object):
    def __init__(self, workflow_key, workflow_id):
        self._workflow_key = workflow_key
        self._workflow_id = workflow_id

    @property
    def workflow_key(self):
        return self._workflow_key

    @workflow_key.setter
    def workflow_key(self, workflow_key):
        self._workflow_key = workflow_key

    @property
    def workflow_id(self):
        return self._workflow_id

    @workflow_id.setter
    def workflow_id(self, workflow_id):
        self._workflow_id = workflow_id


class SubmissionStateWorkflowRun(object):

    STATUS_UNSUBMITTED = "UNSUBMITTED"
    STATUS_SUBMIT_SUCCESS = "SUBMIT_SUCCESS"
    STATUS_SUBMIT_FAIL = "SUBMIT_FAIL"
    STATUS_FINISH_SUCCESS = "FINISH_SUCCESS"
    STATUS_FINISH_FAIL = "FINISH_FAIL"

    VALIDATION_UNSTARTED = "VALIDATION_UNSTARTED"
    VALIDATION_FAIL = "VALIDATION_FAIL"
    VALIDATION_SUCCESS = "VALIDATION_SUCCESS"

    def __init__(
        self, workflow_key, workflow_id, task_key, test_i, engine_key, inputs, outputs
    ):
        self._workflow_key = workflow_key
        self._workflow_id = workflow_id
        self._task_key = task_key
        self._test_i = test_i
        self._engine_key = engine_key
        self._inputs = inputs
        self._outputs = outputs
        self._status = SubmissionStateWorkflowRun.STATUS_UNSUBMITTED
        self._created_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        self._wes_run_id = None
        self._wes_state = None
        self._validation_status = SubmissionStateWorkflowRun.VALIDATION_UNSTARTED
        self._validation_message = ""

    @property
    def status(self):
        return self._status

    def submit_fail(self):
        self._status = SubmissionStateWorkflowRun.STATUS_SUBMIT_FAIL

    def submit_success(self):
        self._status = SubmissionStateWorkflowRun.STATUS_SUBMIT_SUCCESS

    def finish_fail(self):
        self._status = SubmissionStateWorkflowRun.STATUS_FINISH_FAIL

    def finish_success(self):
        self._status = SubmissionStateWorkflowRun.STATUS_FINISH_SUCCESS

    def is_done(self):
        return self._status in set(
            [
                self.__class__.STATUS_SUBMIT_FAIL,
                self.__class__.STATUS_FINISH_SUCCESS,
                self.__class__.STATUS_FINISH_FAIL,
            ]
        )

    @property
    def wes_run_id(self):
        return self._wes_run_id

    @wes_run_id.setter
    def wes_run_id(self, wes_run_id):
        self._wes_run_id = wes_run_id

    @property
    def wes_state(self):
        return self._wes_state

    @wes_state.setter
    def wes_state(self, wes_state):
        self._wes_state = wes_state

    @property
    def validation_status(self):
        return self._validation_status

    @validation_status.setter
    def validation_status(self, validation_status):
        self._validation_status = validation_status

    @property
    def validation_message(self):
        return self._validation_message

    @validation_message.setter
    def validation_message(self, validation_message):
        self._validation_message = validation_message
