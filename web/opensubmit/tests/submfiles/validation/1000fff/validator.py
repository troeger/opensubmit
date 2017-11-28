#! /usr/bin/env python3


def validate(job):
    try:
        job.run_build(inputs=['helloworld.c'], output='helloworld')
        running = job.spawn_program('./helloworld')
        running.expect('Please provide your input: ')
        running.sendline('The quick brown fox')
        running.expect('Your input was: The quick brown fox')
        running.expect_end()
    except Exception as e:
        job.send_result(e)
    else:
        job.send_pass_result('Everything worked. Congratulations!')
