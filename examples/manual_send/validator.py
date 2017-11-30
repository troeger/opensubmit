'''
Example for an OpenSubmit validator.

Install opensubmit-exec and try it out:

opensubmit-exec test examples/manual_send/

You can seen that student submissions may be
ZIP files with nested subdirecories.

This validator manages the result sending by
itself. Exceptions are still not catched and
automatically handled as failed validation.
'''


from opensubmitexec.compiler import GPP


def validate(job):
    job.run_compiler(compiler=GPP, inputs=['sum.cpp'], output='parsum')
    # Alternative, since the student ZIP file has a Makefile
    # job.run_make(mandatory=True)

    exit_code, output = job.run_program(
        './parsum', arguments=['5', '1', '1000000000'])
    if exit_code == 0:
        job.send_pass_result("Good job! Your output: " + output,
                             "Student seems to be capable.")
    else:
        job.send_fail_result("Oops! That went wrong: " + output,
                             "Student needs support.")
