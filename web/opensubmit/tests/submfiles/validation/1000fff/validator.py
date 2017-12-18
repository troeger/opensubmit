from opensubmitexec.helpers import assert_dont_raises


def validate(job):
    student_files = ['helloworld.c']
    assert_dont_raises(job.run_build, inputs=student_files, output='helloworld')
    running = assert_dont_raises(job.spawn_program, './helloworld')
    assert_dont_raises(running.expect, 'Please provide your input: ')
    assert_dont_raises(running.sendline, 'The quick brown fox')
    assert_dont_raises(running.expect, 'Your input was: The quick brown fox')
    assert_dont_raises(running.expect_end)
    job.send_pass_result("We saw the following console interaction:\n\n " + running.get_output())
