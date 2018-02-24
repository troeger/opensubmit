from opensubmitexec.exceptions import TerminationException

test_cases = [
    ['0', '0'],
    ['1', '1'],
    ['8', '1000'],
    ['9', '1001'],
    ['15', '1111']
]

def validate(job):
    job.run_build(inputs=['dec_to_bin.c'], output='dec_to_bin')
    for std_input, expected_output in test_cases:
        running = job.spawn_program('./dec_to_bin')
        running.sendline(std_input)
        try:
            running.expect(expected_output, timeout=1)
        except TerminationException:
            job.send_fail_result("Arrgh, a problem: We expected {0} as output for the input {1}.".format(expected_output, std_input), "wrong output")
            return
        else:
            running.expect_end()
    job.send_pass_result("Everything worked fine!", "Student seems to be capable.")