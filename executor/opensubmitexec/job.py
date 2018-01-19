'''
The official executor API for validation test and full test scripts.
'''

from .internaljob import InternalJob, UNSPECIFIC_ERROR
from .filesystem import has_file
from .exceptions import *
from .compiler import GCC, compiler_cmdline
from .running import RunningProgram

import os
import re
import logging
logger = logging.getLogger('opensubmitexec')


class Job(InternalJob):
    """A OpenSubmit validation job to be done.

    Attributes:
        working_dir (str):            The working directory with all student and test script files.
        timeout (str):                The timeout for execution, as configured in the assignment settings.
        submission_id (str):          The OpenSubmit submission ID.
        file_id (str):                The OpenSubmit submission file ID.
        submitter_name (str):         Real name of the submitting student.
        submitter_student_id (str):   Student ID of the submitting student.
        submitter_studyprogram (str): Study program of the submitting student.
        author_names (str):           Real names of all authors.
        course (str):                 Name of the course for this submission.
        assignment (str):             Name of the assignment for this submission.
    """

    working_dir = None
    timeout = None
    submission_id = None
    file_id = None
    submitter_name = None
    submitter_student_id = None
    submitter_studyprogram = None
    author_names = None
    course = None
    assignment = None

    @property
    # The file name of the validation / full test script
    # on disk, after unpacking / renaming.
    def validator_script_name(self):
        return self.working_dir + self._validator_import_name + '.py'

    def send_fail_result(self, info_student, info_tutor="Test failed."):
        """Reports a negative result for this validation job.

        Args:
            info_student (str): Information for the student(s)
            info_tutor   (str): Information for the tutor(s)

        """
        self._send_result(info_student, info_tutor, UNSPECIFIC_ERROR)

    def send_pass_result(self,
                         info_student="All tests passed. Awesome!",
                         info_tutor="All tests passed."):
        """Reports a positive result for this validation job.

        Args:
            info_student (str): Information for the student(s)
            info_tutor   (str): Information for the tutor(s)

        """
        self._send_result(info_student, info_tutor, 0)

    def delete_binaries(self):
        """Scans for binary files in the student submission and deletes them.

        Returns:
            The list of deleted files.

        """
        raise NotImplementedError

    def run_configure(self, mandatory=True):
        """Runs the 'configure' program in the working directory.

        Args:
            mandatory (bool): Throw exception if 'configure' fails or a
                              'configure' file is missing.

        """
        if not has_file(self.working_dir, 'configure'):
            if mandatory:
                raise FileNotFoundError(
                    "Could not find a configure script for execution.")
            else:
                return
        try:
            prog = RunningProgram(self, 'configure')
            prog.expect_exit_status(0)
        except Exception:
            if mandatory:
                raise

    def run_make(self, mandatory=True):
        """Runs the 'make' program in the working directory.

        Args:
            mandatory (bool): Throw exception if 'make' fails or a
                              'Makefile' file is missing.

        """
        if not has_file(self.working_dir, 'Makefile'):
            if mandatory:
                raise FileNotFoundError("Could not find a Makefile.")
            else:
                return
        try:
            prog = RunningProgram(self, 'make')
            prog.expect_exit_status(0)
        except Exception:
            if mandatory:
                raise

    def run_compiler(self, compiler=GCC, inputs=None, output=None):
        """Runs a compiler in the working directory.

        Args:
            compiler (tuple): The compiler program and its command-line arguments,
                              including placeholders for output and input files.
            inputs (tuple):   The list of input files for the compiler.
            output (str):     The name of the output file.

        """
        # Let exceptions travel through
        prog = RunningProgram(self, *compiler_cmdline(compiler=compiler,
                                                      inputs=inputs,
                                                      output=output))
        prog.expect_exit_status(0)

    def run_build(self, compiler=GCC, inputs=None, output=None):
        """Combined call of 'configure', 'make' and the compiler.

        The success of 'configure' and 'make' is optional.
        The arguments are the same as for run_compiler.

        """
        logger.info("Running build steps ...")
        self.run_configure(mandatory=False)
        self.run_make(mandatory=False)
        self.run_compiler(compiler=compiler,
                          inputs=inputs,
                          output=output)

    def spawn_program(self, name, arguments=[], timeout=30, exclusive=False):
        """Spawns a program in the working directory.

        This method allows the interaction with the running program,
        based on the returned RunningProgram object.

        Args:
            name (str):        The name of the program to be executed.
            arguments (tuple): Command-line arguments for the program.
            timeout (int):     The timeout for execution.
            exclusive (bool):  Prevent parallel validation runs on the
                               test machines, e.g. when doing performance
                               measurements for submitted code.

        Returns:
            RunningProgram: An object representing the running program.

        """
        logger.debug("Spawning program for interaction ...")
        if exclusive:
            kill_longrunning(self.config)

        return RunningProgram(self, name, arguments, timeout)

    def run_program(self, name, arguments=[], timeout=30, exclusive=False):
        """Runs a program in the working directory to completion.

        Args:
            name (str):        The name of the program to be executed.
            arguments (tuple): Command-line arguments for the program.
            timeout (int):     The timeout for execution.
            exclusive (bool):  Prevent parallel validation runs on the
                               test machines, e.g. when doing performance
                               measurements for submitted code.

        Returns:
            tuple: A tuple of the exit code, as reported by the operating system,
            and the output produced during the execution.
        """
        logger.debug("Running program ...")
        if exclusive:
            kill_longrunning(self.config)

        prog = RunningProgram(self, name, arguments, timeout)
        return prog.expect_end()

    def grep(self, regex):
        """Scans the student files for text patterns.

        Args:
            regex (str):       Regular expression used for scanning inside the files.

        Returns:
            tuple:     Names of the matching files in the working directory.
        """
        matches = []
        logger.debug("Searching student files for '{0}'".format(regex))
        for fname in self.student_files:
            if os.path.isfile(self.working_dir + fname):
                for line in open(self.working_dir + fname, 'br'):
                    if re.search(regex.encode(), line):
                        logger.debug("{0} contains '{1}'".format(fname, regex))
                        matches.append(fname)
        return matches

    def ensure_files(self, filenames):
        """Checks the student submission for specific files.

        Args:
            filenames (tuple): The list of file names to be cjecked for.

        Returns:
            bool: Indicator if all files are found in the student archive.
        """
        logger.debug("Testing {0} for the following files: {1}".format(
            self.working_dir, filenames))
        dircontent = os.listdir(self.working_dir)
        for fname in filenames:
            if fname not in dircontent:
                return False
        return True
