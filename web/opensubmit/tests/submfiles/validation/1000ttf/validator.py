from opensubmitexec.helpers import assert_raises, assert_dont_raises


def validate(job):
    student_files = ['helloworld.c']
    assert_dont_raises(job.run_build, inputs=student_files, output='helloworld')
    assert_dont_raises(job.run_compiler, inputs=student_files, output='helloworld')
    assert_dont_raises(job.run_make, mandatory=False)
    assert_raises(job.run_make, mandatory=True)
    assert_dont_raises(job.run_configure, mandatory=False)
    assert_raises(job.run_configure, mandatory=True)
