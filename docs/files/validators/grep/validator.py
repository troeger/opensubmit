from opensubmitexec.exceptions import TimeoutException
from opensubmitexec.exceptions import TerminationException

test_cases = [
    ['hallo', 'ollah'],
    ['1', '1'],
    ['1234', '4321']
]

def validate(job):
    file_names = job.grep('.*for[:space:]*(.*;.*;.*).*')
    if len(file_names) < 1:
        job.send_fail_result("You probably did not use a for-loop.", "Student is not able to use a for-loop.")
        return

    job.run_build(inputs=['reverse.c'], output='reverse')
    for std_input, expected_output in test_cases:
        running = job.spawn_program('./reverse')
        running.sendline(std_input)
        try:
            running.expect(expected_output, timeout=1)
        except TimeoutException:
            job.send_fail_result("Your output took to long!", "timeout")
            return
        except TerminationException:
            job.send_fail_result("The string was not reversed correctly for the following input: " + std_input, "The student does not seem to be capable.")
            return
        else:
            running.expect_end()
    job.send_pass_result("Everything worked fine!", "Student seems to be capable.")