def validate(job):
    job.run_make(mandatory=True)
    exit_code, output = job.run_program('./hello')
    if output.strip() == "hello world":
        job.send_pass_result("The world greets you! Everything worked fine!")
    else:
        job.send_fail_result("Wrong output: " + output)