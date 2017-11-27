'''
    Functions related to command execution on the local host.
'''


import os
import sys
import platform
import subprocess
import time

from .result import FailResult, PassResult

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


def shell_execution(cmdline, working_dir, timeout=None):
    '''
    Run given shell command in the given working directory with the
    given timeout. Return according result object.

    cmdline is an array.
    '''

    # Allow code to load its own libraries
    os.environ["LD_LIBRARY_PATH"] = working_dir

    cmd_text = ' '.join(cmdline)

    logger.debug("Let's execute '{0}' in {1} ...".format(cmd_text, working_dir))

    try:
        if platform.system() == "Windows":
            proc = subprocess.Popen(cmdline,
                                    cwd=working_dir,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                                    universal_newlines=True)
        else:
            proc = subprocess.Popen(cmdline,
                                    cwd=working_dir,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    preexec_fn=os.setsid,
                                    universal_newlines=True)
        output = None

        try:
            got_timeout = False
            output, stderr = proc.communicate(timeout=timeout)
            logger.debug("Execution finished in time.")
        except subprocess.TimeoutExpired:
            got_timeout = True

        if output is None:
            output = ""

    except FileNotFoundError:
        details = "Tried to execute '%s', but this file cannot be found."%(cmd_text)
        logger.info(details)
        return FailResult(info_student=details)

    except Exception:
        details = "Execution of '{0}' failed: {1}".format(cmd_text, str(sys.exc_info()))
        logger.info(details)
        return FailResult(info_student=details)

    else:
        dircontent = str(os.listdir(working_dir))
        logger.debug("Working directory after execution: " + dircontent)

        # No exception, but timeout, so we still have no error code
        if got_timeout:
            details = "Execution of '{0}' was terminated because it took too long ({1} seconds).\n".format(cmd_text, timeout)
            details += "This was the output so far: \n{0}\n".format(output)
            return FailResult(info_student=details)

        # Ok, it seems like we got a legitimate error code
        details = "Execution of '{0}' finished with error code {1}.\n".format(cmd_text, proc.returncode)
        details += "This was the output: \n{0}\n".format(output)
        details += "The working directory now looks like this: \n{0}".format(dircontent)

        if proc.returncode == 0:
            res = PassResult(details)
        else:
            res = FailResult(info_student=details, error_code=proc.returncode)
        return res
