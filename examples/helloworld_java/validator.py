from opensubmitexec.compiler import JAVAC


def validate(job):
    job.run_compiler(compiler=JAVAC, inputs=['HelloWorld.java'])

    # Run the compilation result.
    job.run_program('java HelloWorld')
