import pexpect
import os
import time
import tempfile

from .exceptions import *

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
    """A running program that you can interact with.

    This class is a thin wrapper around the functionality
    of pexpect (http://pexpect.readthedocs.io/en/stable/overview.html).

    Attributes:
        job (Job):            The original job for this program execution.
        name (str):           The name of the binary that is executed.
        arguments (tuple):    The command-line arguments being used for execution.
    """
    job = None
    name = None
    arguments = None
    _logfile = None
    _spawn = None

    def get_output(self):
        """Get the program output produced so far.

        Returns:
            str: Program output as text. May be incomplete.
        """
        # Open temporary file for reading, in text mode
        # This makes sure that the file pointer for writing
        # is not touched
        return ''.join(open(self._logfile.name).readlines())

    def get_exitstatus(self):
        """Get the exit status of the program execution.

        Returns:
            int: Exit status as reported by the operating system,
                 or None if it is not available.
        """
        logger.debug("Exit status is {0}".format(self._spawn.exitstatus))
        return self._spawn.exitstatus

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

        self._logfile = tempfile.NamedTemporaryFile()
        logger.debug("Keeping console I/O in " + self._logfile.name)
        try:
            self._spawn = pexpect.spawn(name, arguments,
                                        logfile=self._logfile,
                                        timeout=timeout,
                                        cwd=self.job.working_dir,
                                        echo=False)
        except Exception as e:
            logger.debug("Spawning failed: " + str(e))
            raise NestedException(instance=self, real_exception=e, output=self.get_output())

    def expect_output(self, pattern, timeout=-1):
        """Wait until the running program performs some given output, or terminates.

        Args:
            pattern:  The pattern the output should be checked for.
            timeout (int):  How many seconds should be waited for the output.

        The pattern argument may be a string, a compiled regular expression,
        or a list of any of those types. Strings will be compiled into regular expressions.

        Returns:
            int: The index into the pattern list. If the pattern was not a list, it returns 0 on a successful match.

        Raises:
            TimeoutException: The output did not match within the given time frame.
            TerminationException: The program terminated before producing the output.
            NestedException: An internal problem occured while waiting for the output.
        """
        logger.debug("Expecting output '{0}' from '{1}'".format(pattern, self.name))
        try:
            return self._spawn.expect(pattern, timeout)
        except pexpect.exceptions.EOF as e:
            logger.debug("Raising termination exception.")
            raise TerminationException(instance=self, real_exception=e, output=self.get_output())
        except pexpect.exceptions.TIMEOUT as e:
            logger.debug("Raising timeout exception.")
            raise TimeoutException(instance=self, real_exception=e, output=self.get_output())
        except Exception as e:
            logger.debug("Expecting output failed: " + str(e))
            raise NestedException(instance=self, real_exception=e, output=self.get_output())

    def sendline(self, text):
        """Sends an input line to the running program, including os.linesep.

        Args:
            text (str): The input text to be send. 

        Raises:
            TerminationException: The program terminated before / while / after sending the input.
            NestedException: An internal problem occured while waiting for the output.
        """
        logger.debug("Sending input '{0}' to '{1}'".format(text, self.name))
        try:
            return self._spawn.sendline(text)
        except pexpect.exceptions.EOF as e:
            logger.debug("Raising termination exception.")
            raise TerminationException(instance=self, real_exception=e, output=self.get_output())
        except pexpect.exceptions.TIMEOUT as e:
            logger.debug("Raising timeout exception.")
            raise TimeoutException(instance=self, real_exception=e, output=self.get_output())
        except Exception as e:
            logger.debug("Sending input failed: " + str(e))
            raise NestedException(instance=self, real_exception=e, output=self.get_output())

    def expect_end(self):
        """Wait for the running program to finish.

        Returns:
            A tuple with the exit code, as reported by the operating system, and the output produced.
        """
        logger.debug("Waiting for termination of '{0}'".format(self.name))
        try:
            # Make sure we fetch the last output bytes.
            # Recommendation from the pexpect docs.
            self._spawn.expect(pexpect.EOF)
            self._spawn.wait()
            dircontent = str(os.listdir(self.job.working_dir))
            logger.debug("Working directory after execution: " + dircontent)
            return self.get_exitstatus(), self.get_output()
        except pexpect.exceptions.EOF as e:
            logger.debug("Raising termination exception.")
            raise TerminationException(instance=self, real_exception=e, output=self.get_output())
        except pexpect.exceptions.TIMEOUT as e:
            logger.debug("Raising timeout exception.")
            raise TimeoutException(instance=self, real_exception=e, output=self.get_output())
        except Exception as e:
            logger.debug("Waiting for expected program end failed.")
            raise NestedException(instance=self, real_exception=e, output=self.get_output())

    def expect_exitstatus(self, exit_status):
        """Wait for the running program to finish and expect some exit status.

        Args:
            exit_status (int):  The expected exit status.

        Raises:
            WrongExitStatusException: The produced exit status is not the expected one.
        """
        self.expect_end()
        logger.debug("Checking exit status of '{0}', output so far: {1}".format(
            self.name, self.get_output()))
        if self._spawn.exitstatus is None:
            raise WrongExitStatusException(
                instance=self, expected=exit_status, output=self.get_output())

        if self._spawn.exitstatus is not exit_status:
            raise WrongExitStatusException(
                instance=self,
                expected=exit_status,
                got=self._spawn.exitstatus,
                output=self.get_output())

    def expect_exit_status(self, exit_status):
        """
        Deprecated. Use expect_exitstatus() instead.
        """
        return self.expect_exitstatus(exit_status)

    def expect(self, pattern, timeout=-1):
        """
        Deprecated. Use expect_output() instead.
        """
        return self.expect_output(pattern, timeout)
