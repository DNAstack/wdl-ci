from datetime import datetime

class SubmissionSet(object):
    
    def __init__(self):
        self.submissions = []
    
    def add_submission(self, workflow, task, test_case):
        self.submissions.append(Submission(workflow, task, test_case))
    
    def submit_all(self):
        # TODO: implement dummy method
        for submission in self.submissions:
            submission.set_status_submitted()

class Submission(object):

    STATUS_UNSUBMITTED = 0
    STATUS_SUBMITTED = 1
    STATUS_FINISHED_SUCCESS = 2
    STATUS_FINISHED_FAIL = 3

    def __init__(self, workflow, task, test_case):
        self.workflow = workflow
        self.task = task
        self.test_case = test_case
        self.status = Submission.STATUS_UNSUBMITTED
        self.created_at = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    
    def set_status_unsubmitted(self):
        self.status = Submission.STATUS_UNSUBMITTED
    
    def set_status_submitted(self):
        self.status = Submission.STATUS_SUBMITTED
