from opensubmitexec.compiler import JAVAC


def validate(job):

    if not job.ensure_files(['HelloWorld.java']):
        job.send_fail_result("Your submitted file must be named 'HelloWorld.java'.", "Student used wrong file name.")

    job.run_compiler(compiler=JAVAC, inputs=['HelloWorld.java'])

    # Run the compilation result.
    job.run_program('java HelloWorld')
