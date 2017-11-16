#! /usr/bin/env python3

def validate(job):
	student_files = ['sum.cpp']
	result = job.run_make()
	job.send_result(result)

