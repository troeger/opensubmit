'''
    Functions related to command execution on the local host.
'''


import os
import time

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
