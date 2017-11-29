from opensubmitexec.helpers import assert_raises, assert_dont_raises
from opensubmitexec import compiler


def validate(job):
    student_files = ['helloworld.c']
    assert_dont_raises(job.run_build, inputs=student_files, output='helloworld')
