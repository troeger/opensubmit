def validate(job):
    student_files = ['helloworld.c']
    job.run_build(inputs=student_files, output='helloworld')
    job.run_program('./helloworld', timeout=2)
