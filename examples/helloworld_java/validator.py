from opensubmitexec.compiler import JAVAC


def validate(job):

    # Make sure that the right file name is given
    job.ensure_files(['HelloWorld.java'])

    # Run the compiler
    job.run_compiler(compiler=JAVAC, inputs=['HelloWorld.java'])

    # Run the compilation result.
    job.run_program('java HelloWorld')
