'''
Example for an OpenSubmit validator.

Install opensubmit-exec and try it out:

opensubmit-exec test examples/io_fail/

It is shown how you can interact with
a running student program and can handle
the exceptional situations by yourself.
'''

from opensubmitexec.exceptions import TimeoutException


def validate(job):
    job.run_build(inputs=['helloworld.c'], output='helloworld')
    running = job.spawn_program('./helloworld')
    try:
        running.expect('Please provide your input: XXX', timeout=1)
    except TimeoutException:
        job.send_fail_result("Your output took to long", "timeout")
    else:
        running.sendline('The quick brown fox')
        running.expect('Your input was: The quick brown fox')
        running.expect_end()
