#! /usr/bin/env python3

from opensubmit.executor import TestJob

def validate(submission):
	submission.run_compiler()
	exec_info = submission.run_binary(args=None, timeout=30, exclusive=False)
	submission.send_result(exec_info)

if __name__ == "__main__":
	test_job = TestJob(from_dir='.')
	validate(test_job)
