#! /usr/bin/env python3


def validate(job):
    student_files = ['helloworld.c']
    result = job.run_build(inputs=student_files, output='helloworld')
    job.send_result(result)
