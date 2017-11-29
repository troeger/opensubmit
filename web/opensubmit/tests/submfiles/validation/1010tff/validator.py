from opensubmitexec.helpers import assert_raises, assert_dont_raises
from opensubmitexec import compiler


def validate(job):
    student_files = ['sum.cpp']
    assert_dont_raises(job.run_build, compiler=compiler.GPP, inputs=student_files, output='sum1')
    assert_dont_raises(job.run_compiler, compiler=compiler.GPP, inputs=student_files, output='sum2')
    assert_dont_raises(job.run_make, mandatory=False)
    assert_dont_raises(job.run_make, mandatory=True)
    assert_dont_raises(job.run_configure, mandatory=False)
    assert_raises(job.run_configure, mandatory=True)
