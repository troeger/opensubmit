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
    """A OpenSubmit validation job to be done,
       including helper functions for the
       validation.

    Attributes:
        working_dir (str):            The working directory for this job.
        timeout (str):                The timeout for execution, as demanded by the assignment.
        submission_id (str):          The unique OpenSubmit submission ID.
        file_id (str):                The unique OpenSubmit submission file ID.
        submitter_name (str):         Name of the submitting student.
        submitter_student_id (str):   Student ID of the submitting student.
        submitter_studyprogram (str): Name of the study program of the submitter.
        author_names (str):           Names of the submission authors.
        course (str):                 Name of the course where this submission happened.
        assignment (str):             Name of the assignment for which this submission happened.
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

    def send_fail_result(self, info_student, info_tutor):
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
            RunningProgram object

        """
        logger.debug("Spawning program for interaction ...")
        if exclusive:
            kill_longrunning(self.config)

        return RunningProgram(self, name, arguments, timeout)

    def run_program(self, name, arguments=[], timeout=30, exclusive=False):
        '''
        Runs a program in the working directory.
        The result is a tuple of exit code and output.

        The caller can demand exclusive execution on this machine.
        '''
        logger.debug("Running program ...")
        if exclusive:
            kill_longrunning(self.config)

        prog = RunningProgram(self, name, arguments, timeout)
        return prog.expect_end()

    def grep(self, regex):
        '''
        Searches the student files in self.working_dir for files
        containing a specific regular expression.

        Returns the names of the matching files as list.
        '''
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
        '''
        Searches the student submission for specific files.
        Expects a list of filenames. Returns a boolean indicator.
        '''
        logger.debug("Testing {0} for the following files: {1}".format(
            self.working_dir, filenames))
        dircontent = os.listdir(self.working_dir)
        for fname in filenames:
            if fname not in dircontent:
                return False
        return True
