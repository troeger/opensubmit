#! /usr/bin/env python3

from opensubmitexec import compiler

def validate(job):
	student_files = ['sum.cpp']
	result = job.run_compiler(compiler=compiler.GPP, inputs=student_files, output='sum')
	job.send_result(result)
