#! /usr/bin/env python3

def validate(job):
	student_files = ['python.pdf']
	result = job.ensure_files(student_files)
	job.send_result(result)
