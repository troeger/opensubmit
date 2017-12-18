from opensubmitexec.helpers import assert_raises, assert_dont_raises


def validate(job):
    student_files = ['python.pdf']
    assert_raises(job.run_build, inputs=student_files, output='helloworld')
    assert_raises(job.run_compiler, inputs=student_files, output='helloworld')
    assert_dont_raises(job.run_make, mandatory=False)
    assert_raises(job.run_make, mandatory=True)
    assert_dont_raises(job.run_configure, mandatory=False)
    assert_raises(job.run_configure, mandatory=True)

    # Add some explicit checks about the working directory.
    # Mainly intended to test if file download keeps
    # the original file names appropriately (see #194)
    import os
    assert(os.path.isfile(job.working_dir + os.sep + 'validator.py'))
    assert(os.path.isfile(job.working_dir + os.sep + 'python.pdf'))
