#! /usr/bin/env python3


def validate(job):
    student_files = ['python.pdf']
    try:
        job.run_build(inputs=student_files, output='helloworld')
    except Exception:
        pass
    else:
        assert(False)

    try:
        job.run_compiler(inputs=student_files, output='helloworld')
    except Exception:
        pass
    else:
        assert(False)

    job.run_make(mandatory=False)

    try:
        job.run_make(mandatory=True)
    except Exception:
        pass
    else:
        assert(False)

    job.run_configure(mandatory=False)

    try:
        job.run_configure(mandatory=True)
    except Exception:
        pass
    else:
        assert(False)
