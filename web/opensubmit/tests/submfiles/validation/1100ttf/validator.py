from opensubmitexec.helpers import assert_raises, assert_dont_raises
from opensubmitexec import compiler


def validate(job):
    student_files = ['helloworld.c']
    assert_dont_raises(job.run_build, compiler=compiler.GPP, inputs=student_files, output='helloworld')
    assert_dont_raises(job.run_compiler, compiler=compiler.GPP, inputs=student_files, output='helloworld')
    assert_dont_raises(job.run_make, mandatory=False)
    assert_raises(job.run_make, mandatory=True)
    assert_dont_raises(job.run_configure, mandatory=False)
    assert_raises(job.run_configure, mandatory=True)
