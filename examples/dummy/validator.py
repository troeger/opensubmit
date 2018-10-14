'''
Example for an OpenSubmit validator.

Install opensubmit-exec and try it out:

opensubmit-exec test examples/dummy/
'''

def validate(job):
    student_info = "Greetings from the dummy validator. This is the feedback for the student."
    teacher_info = "Greetings from the dummy validator. This is the feedback for the teacher."
    job.send_pass_result(student_info, teacher_info)
