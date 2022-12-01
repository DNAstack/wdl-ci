import jsonpickle
import os
import sys
from wdltest.constants import *
from wdltest.exception.wdl_test_cli_exit_exception import WdlTestCliExitException
from wdltest.model.changeset import Changeset
from wdltest.model.testset import TestSet
from wdltest.model.submission_set import SubmissionSet, Submission

def validate_input(kwargs):
    if not kwargs['all']:
        if not os.path.exists(CHANGES_JSON):
            raise WdlTestCliExitException(f"cannot determine changed tasks, {CHANGES_JSON} not found", 1)

def submit_handler(kwargs):
    try:
        validate_input(kwargs)
        testset = TestSet.from_json(TESTS_JSON)
        changeset = Changeset.from_json(CHANGES_JSON)
        submission_set = SubmissionSet()
        
        for workflow_key in changeset.get_workflow_keys():
            for task in changeset.get_tasks(workflow_key):
                for test_case in testset.get_task_tests(workflow_key, task):
                    submission_set.add_submission(workflow_key, task, test_case)
        
        # submit all WDL jobs
        submission_set.submit_all()

        # validate all jobs were successfully submitted
        for submission in submission_set.submissions:
            if submission.status != Submission.STATUS_SUBMITTED:
                raise WdlTestCliExitException(f"test case was not submitted successfully. workflow: {submission.workflow}, task: {submission.task}.", 1)
        
        submission_set_encoded = jsonpickle.encode(submission_set)
        open(SUBMISSION_JSON, "w").write(submission_set_encoded)

    except WdlTestCliExitException as e:
        print(f"exiting with code {e.exit_code}, message: {e.message}")
        sys.exit(e.exit_code)
