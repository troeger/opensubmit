import pexpect
import os

from .exceptions import RunningProgramException

import logging
logger = logging.getLogger('opensubmitexec')


class RunningProgram(pexpect.spawn):
    '''
    A running program that can be interacted with.

    This class is a thin wrapper around the functionality
    of pexpect (http://pexpect.readthedocs.io/en/stable/overview.html).
    '''

    def __init__(self, job, name, arguments=None, timeout=30):
        self.job = job

        # Allow code to load its own libraries
        os.environ["LD_LIBRARY_PATH"] = job.working_dir

        logger.debug("Let's execute '{0}' in {1} ...".format(name, job.working_dir))

        # Sometimes the EOF exception happens before all output
        # was collected. Check the pexpect FAQ.
        # The internet says that this hack helps.
        arguments = ['-c', name] + arguments

        try:
            self._spawn = pexpect.spawn('bash',
                                        args=arguments,
                                        timeout=timeout,
                                        cwd=self.job.working_dir)
        except Exception as e:
            raise RunningProgramException(self, e)

    def expect(self, pattern):
        '''
        Expect an output pattern from the running program.
        '''
        try:
            return self._spawn.expect(pattern)
        except Exception as e:
            raise RunningProgramException(self, e)

    def sendline(self, pattern):
        '''
        Send input to the running program.
        '''
        try:
            return self._spawn.sendline(pattern)
        except Exception as e:
            raise RunningProgramException(self, e)

    def expect_end(self):
        '''
        Wait for the program to finish.
        '''
        try:
            # Make sure we fetch the last output bytes.
            # Recommendation from the pexpect docs.
            self._spawn.expect(pexpect.EOF)
            self._spawn.wait()
            dircontent = str(os.listdir(self.job.working_dir))
            logger.debug("Working directory after execution: " + dircontent)
        except Exception as e:
            raise RunningProgramException(self, e)
