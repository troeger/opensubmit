# see https://github.com/troeger/opensubmit/issues/229

from opensubmitexec.helpers import assert_raises

test_cases = [
    ["2 0 0 0 1 0", "1"],
]


def validate(job):
    job.run_compiler(inputs=['bsp.c'], output='bsp')
    running = job.spawn_program('./bsp')
    for std_input, expected_output in test_cases:
        running.sendline(std_input)
        # Program input contains "1", but output is "0",
        # so a TerminationException should be raised
        assert_raises(running.expect, expected_output, timeout=1)
        job.send_fail_result("timeout", "timeout")
