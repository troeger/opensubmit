'''
    Functions related to command execution on the local host.
'''

from .submission import Submission
from .result import FailResult, Result

import logging
logger = logging.getLogger('opensubmit.executor')

import os, sys, platform, subprocess, signal
from threading import Timer

def kill_longrunning(config):
    '''
        Terminate everything under the current user account that has run too long.
        This is a final safeguard if the SIGALRM stuff is not working.
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


def _handle_alarm(proc):
    '''
        Signal handler for timeout implementation
    '''
    logger.info("Got alarm signal, killing %d due to timeout." % proc.pid)
    try:
        if platform.system() == "Windows":
            proc.terminate()
        else:
            os.killpg(proc.pid, signal.SIGTERM)
    except Exception as e:
        logger.error("Error while killing process %d" % proc.pid)

def run(sub: Submission):
    '''
        Perform some execution activity with timeout support.
        Returns Result object.
    '''
    cmdline_text=sub._config.get("Execution","script_runner")+' '+sub.validator
    cmdline=cmdline_text.split(' ')    # Support cmd-arguments in config setting

    dircontent = os.listdir(sub.working_dir)
    logger.debug("Working directory before start: " + str(dircontent))

    logger.info("Spawning process for validator: " + str(cmdline))
    
    try:
        if platform.system() == "Windows":
            proc = subprocess.Popen(cmdline, cwd=sub.working_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        else:
            proc = subprocess.Popen(cmdline, cwd=sub.working_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, preexec_fn=os.setsid)
        logger.debug("Starting termination timer with %u seconds" % sub.timeout)
        timer = Timer(sub.timeout, _handle_alarm, args = [proc])
        timer.start()
        output = None
        stderr = None
        
        try:
            output, stderr = proc.communicate()
            logger.debug("Process regularly terminated")
        except Exception as e:
            logger.debug("Process potentially killed by timeout: " + str(e))
        
        if output == None:
            output = ""
        else:
            output = output.decode("utf-8",errors="ignore")
            
        if stderr == None:
            stderr = ""
        else:
            stderr = stderr.decode("utf-8",errors="ignore")
        
        try:
            logger.debug("Stopping termination timer")
            timer.cancel()
        except Exception as e:
            logger.error("Error while stopping termination timer:" + str(e))
            return FailResult("Internal error with termination timer stopping.")
    except Exception:
        details = str(sys.exc_info())
        logger.info("Exception on process execution: " + details)
        return FailResult("Error on execution: "+details)

    logger.info("Executed with error code {0} \n\n".format(proc.returncode))
    dircontent = os.listdir(sub.working_dir)
    logger.debug("Working directory after finishing: " + str(dircontent))

    if (proc.returncode == 0-signal.SIGTERM) or (proc.returncode == None):
        res=FailResult("Validation was terminated because it took too long (%u seconds). Output so far:\n\n%s"%(timeout,output))
    else:
        res = Result()
        res.error_code=proc.returncode
        res.stdout=output+"\n\nDirectory content as I see it:\n\n" + str(dircontent)
        res.stderr=stderr

    return res



