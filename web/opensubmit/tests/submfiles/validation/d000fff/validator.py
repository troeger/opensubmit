#! /usr/bin/env python3


def validate(job):
    student_files = ['helloworld.c']
    result = job.run_build(inputs=student_files, output='helloworld')
    assert(result.is_ok())
    result = job.run_binary('helloworld')
    job.send_result(result)
    