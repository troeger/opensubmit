'''
    Functions related to command execution on the local host.
'''

from .result import Result, PassResult, FailResult


import logging
logger = logging.getLogger('opensubmit.executor')

import os, sys, platform, subprocess, signal
from threading import Timer

def kill_longrunning(config):
    '''
        Terminate everything under the current user account that has run too long.
        This is a final safeguard if the subprocess timeout stuff is not working.
        You better have no production servers running also under the current user account ...
    '''
    import psutil 
    ourpid = os.getpid()
    username = psutil.Process(ourpid).username
    # check for other processes running under this account
    timeout = config.getint("Execution","timeout")
    for proc in psutil.process_iter():
        if proc.username == username and proc.pid != ourpid:
            runtime = time.time() - proc.create_time
            logger.debug("This user already runs %u for %u seconds." % (proc.pid, runtime))
            if runtime > timeout:
                logger.debug("Killing %u due to exceeded runtime." % proc.pid)
                try:
                    proc.kill()
                except Exception as e:
                    logger.error("ERROR killing process %d." % proc.pid)


def shell_execution(cmdline, working_dir, timeout=999999):
    '''
    Run given shell command in the given working directory with the given timeout.
    Return according result object.
    '''
    got_timeout = False
    # Allow code to load its own libraries
    os.environ["LD_LIBRARY_PATH"]=working_dir
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
            output, stderr = proc.communicate(timeout=timeout)
            logger.debug("Process regulary finished.")
        except subprocess.TimeoutExpired as e:
            got_timeout = True
            logger.debug("Process killed by timeout: " + str(e))
        
        if output == None:
            output = ""
            
    except Exception:
        details = str(sys.exc_info())
        logger.info("Exception on process execution: " + details)
        return FailResult("Internal error on execution: "+details)

    logger.info("Executed {0} with error code {1}.".format(cmdline, proc.returncode))
    if proc.returncode!=0:
        logger.debug("Output of the failed execution:\n"+output)
    dircontent = os.listdir(working_dir)
    logger.debug("Working directory after execution: " + str(dircontent))

    if got_timeout:
        res=FailResult("Execution was terminated because it took too long (%u seconds). Output so far:\n\n%s"%(timeout,output))
    else:
        text = 'Execution of "{0}" ended with error code {1}.\n{2}\nDirectory content as I see it:\n{3}'.format(
               ' '.join(cmdline),
               proc.returncode,
               output,
               str(dircontent))
        if proc.returncode == 0:
            res = PassResult(text)
        else:
            res = FailResult(text)
            res.error_code=proc.returncode
    return res
