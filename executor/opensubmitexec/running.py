import pexpect
import os
import time
import sys

from .exceptions import RunningProgramException, WrongExitStatusException, NestedException

import logging
logger = logging.getLogger('opensubmitexec')


def kill_longrunning(config):
    '''
        Terminate everything under the current user account
        that has run too long. This is a final safeguard if
        the subprocess timeout stuff is not working.
        You better have no production servers running also
        under the current user account ...
    '''
    import psutil
    ourpid = os.getpid()
    username = psutil.Process(ourpid).username
    # Check for other processes running under this account
    # Take the timeout definition from the config file
    timeout = config.getint("Execution", "timeout")
    for proc in psutil.process_iter():
        if proc.username == username and proc.pid != ourpid:
            runtime = time.time() - proc.create_time
            logger.debug("This user already runs %u for %u seconds." %
                         (proc.pid, runtime))
            if runtime > timeout:
                logger.debug("Killing %u due to exceeded runtime." % proc.pid)
                try:
                    proc.kill()
                except Exception:
                    logger.error("ERROR killing process %d." % proc.pid)


class RunningProgram(pexpect.spawn):
    '''
    A running program that can be interacted with.

    This class is a thin wrapper around the functionality
    of pexpect (http://pexpect.readthedocs.io/en/stable/overview.html).
    '''
    job = None
    name = None
    arguments = None

    def __init__(self, job, name, arguments=[], timeout=30):
        self.job = job
        self.name = name
        self.arguments = arguments

        # Allow code to load its own libraries
        os.environ["LD_LIBRARY_PATH"] = job.working_dir

        logger.debug("Spawning '{0}' in {1} with the following arguments:{2}".format(
            name,
            job.working_dir,
            str(arguments)))

        if name.startswith('./'):
            name = name.replace('./', self.job.working_dir)

        try:
            self._spawn = pexpect.spawn(name, arguments,
                                        timeout=timeout,
                                        cwd=self.job.working_dir)
        except Exception as e:
            logger.debug("Spawning failed: " + str(e))
            raise NestedException(self, e)

    def expect(self, pattern):
        '''
        Expect an output pattern from the running program.
        '''
        logger.debug("Expecting output '{0}' from '{1}'".format(pattern, self.name))
        try:
            return self._spawn.expect(pattern)
        except pexpect.exceptions.EOF:
            raise
        except pexpect.exceptions.TIMEOUT:
            raise
        except Exception as e:
            logger.debug("Expecting output failed: " + str(e))
            raise NestedException(self, e)

    def sendline(self, pattern):
        '''
        Send input to the running program.
        '''
        logger.debug("Sending input '{0}' to '{1}'".format(pattern, self.name))
        try:
            return self._spawn.sendline(pattern)
        except pexpect.exceptions.EOF:
            raise
        except pexpect.exceptions.TIMEOUT:
            raise
        except Exception as e:
            logger.debug("Sending input failed: " + str(e))
            raise NestedException(self, e)

    def expect_end(self):
        '''
        Wait for the program to finish, regardless of 
        error code.
        '''
        logger.debug("Waiting for termination of '{0}'".format(self.name))
        try:
            # Make sure we fetch the last output bytes.
            # Recommendation from the pexpect docs.
            self._spawn.expect(pexpect.EOF)
            self._spawn.wait()
            dircontent = str(os.listdir(self.job.working_dir))
            logger.debug("Working directory after execution: " + dircontent)
        except Exception as e:
            logger.debug("Waiting for expected program end failed.")
            raise NestedException(self, e)

    def expect_exit_status(self, exit_status):
        '''
        Wait for the program to finish and expect some
        exit status. Throws exception otherwise.
        '''
        self.expect_end()
        logger.debug("Checking exit status of '{0}', output so far: {1}".format(self.name, self._spawn.before))
        if self._spawn.exitstatus is None:
            raise WrongExitStatusException(self, exit_status)

        if self._spawn.exitstatus is not exit_status:
            raise WrongExitStatusException(self, exit_status, self._spawn.exitstatus)
