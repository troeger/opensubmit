from opensubmitexec.compiler import GCC

test_cases = [
    [['1', '2'], '3'],
    [['-1', '-2'], '-3'],
    [['-2', '2'], '0'],
    [['4', '-10'], '-6'],
    [['4'], 'Wrong number of arguments!'],
    [['1', '1', '1'], 'Wrong number of arguments!']
]

def validate(job):
    job.run_compiler(compiler=GCC, inputs=['sum.c'], output='sum')
    for arguments, expected_output in test_cases:
        exit_code, output = job.run_program('./sum', arguments)
        if output.strip() != expected_output:
            job.send_fail_result("Oops! That went wrong! Input: " + str(arguments) + ", Output: " + output, "Student needs support.")
            return
    job.send_pass_result("Good job! Your program worked as expected!", "Student seems to be capable.")