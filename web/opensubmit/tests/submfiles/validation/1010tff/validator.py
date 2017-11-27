#! /usr/bin/env python3

from opensubmitexec import compiler


def validate(job):
    student_files = ['sum.cpp']

    result = job.run_build(compiler=compiler.GPP,
                           inputs=student_files,
                           output='sum1')
    assert(result.is_ok())

    result = job.run_compiler(compiler=compiler.GPP,
                              inputs=student_files,
                              output='sum2')
    assert(result.is_ok())

    result = job.run_make(mandatory=False)
    assert(result.is_ok())

    result = job.run_make(mandatory=True)
    assert(result.is_ok())

    result = job.run_configure(mandatory=False)
    assert(result.is_ok())

    result = job.run_configure(mandatory=True)
    assert(not result.is_ok())
