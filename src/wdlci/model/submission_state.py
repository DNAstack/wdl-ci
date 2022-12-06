from datetime import datetime

class SubmissionState(object):
    
    def __init__(self):
        self.workflows = {}
        self.workflow_runs = {}
    
    def add_workflow(self, workflow_key, workflow_id):
        self.workflows[workflow_key] = SubmissionStateWorkflow(workflow_key, workflow_id)
    
    def add_workflow_run(self, workflow_key, task_key, test_i, engine_key, inputs, outputs):
        submission_workflow_run = SubmissionStateWorkflowRun(workflow_key, task_key, test_i, engine_key, inputs, outputs)
        self.submissions.append(submission_workflow_run)
    
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

    STATUS_UNSUBMITTED = 0
    STATUS_SUBMITTED = 1
    STATUS_FINISHED_SUCCESS = 2
    STATUS_FINISHED_FAIL = 3

    def __init__(self, workflow_key, task_key, test_i, engine_key, inputs, outputs):
        self._workflow_key = workflow_key
        self._task_key = task_key
        self._test_i = test_i
        self._engine_key = engine_key
        self._inputs = inputs
        self._outputs = outputs
        self._status = SubmissionStateWorkflowRun.STATUS_UNSUBMITTED
        self._created_at = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        self._workflow_run_id = None
    
    def set_status_unsubmitted(self):
        self._status = SubmissionStateWorkflowRun.STATUS_UNSUBMITTED
    
    def set_status_submitted(self):
        self._status = SubmissionStateWorkflowRun.STATUS_SUBMITTED
    
    @property
    def workflow_run_id(self):
        return self._workflow_run_id
    
    @property
    def workflow_run_id(self, workflow_run_id):
        self._workflow_run_id = workflow_run_id
