'''
    Everything that is about to be executed on a test machine.
'''

from urllib import urlencode
from urllib2 import urlopen, HTTPError
import logging, json
import zipfile, tarfile
import tempfile, os, shutil, subprocess, signal, stat, sys, fcntl, pickle, ConfigParser
import time
from datetime import datetime, timedelta

logger=logging.getLogger('OpenSubmitExecutor')

def read_config(config_file):
    '''
        Fill config dictionary, already check and interpret some values.
    '''
    config = ConfigParser.RawConfigParser()
    config.readfp(open(config_file))

    if config.getboolean("Logging","to_file"):
        handler = logging.FileHandler('/tmp/executor.log')
    else:
        handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(config.get("Logging","format")))
    logger.addHandler(handler)
    logger.setLevel(config.get("Logging","level"))

    targetdir=config.get("Execution","directory")
    assert(targetdir.startswith('/'))
    assert(targetdir.endswith('/'))
    return config

def _send_result(config, msg, error_code, submission_file_id, action, perfdata=None):
    ''' 
        Send some result to the OpenSubmit web server.
    '''
    if len(msg)>10000:
        # We need to truncate excessive console output, 
        # since this goes into the database.
        msg=msg[1:10000]
        msg+="\n[Output truncated]"
    if not perfdata:
        perfdata=""
    logger.info("Test for submission file %s completed with error code %s: %s"%(submission_file_id, str(error_code), msg))
    # There are cases where the program was not finished, but we still deliver a result
    # Transmitting "None" is a bad idea, so we use a special code instead
    if error_code==None:
        error_code=-9999    
    # Prepare response HTTP package
    post_data = [('SubmissionFileId',submission_file_id),('Message',msg),('ErrorCode',error_code),('Action',action),('PerfData',perfdata)]    
    try:
        post_data = urlencode(post_data)
        post_data = post_data.encode('utf-8')
        urlopen('%s/jobs/secret=%s'%(config.get("Server","url"), config.get("Server","secret")), post_data)  
    except HTTPError as e:
        logging.error(str(e))

def _infos_opencl():
    '''
        Determine some system information about the installed OpenCL device.
    '''
    result=[]
    try:
        import pyopencl as ocl
        for platform in ocl.get_platforms():
            result.append("Platform: "+platform.name)
            for device in platform.get_devices():
                result.append("    Device:" + device.name.strip())
                infoset = [key for key in dir(device) if not key.startswith('__') and key not in ["extensions", "name"]]
                for attr in infoset:
                    try:
                        result.append("        %s: %s"%(attr.strip(), getattr(device, attr).strip()))
                    except:
                        pass
        return "\n".join(result)
    except:
        return ""

def _infos_cmd(cmd):
    '''
        Determine some system information based on a shell command.
    '''
    try:
        out = subprocess.check_output(cmd+" 2>&1", shell=True)
        out = out.decode("utf-8")
        return out
    except:
        return ""

def _fetch_job(config):
    '''
        Fetch any available work from the OpenSubmit server.
        Returns job information as function result tuple:
            fname     - Fully qualified temporary file name for the job file
            submid    - ID of this file on the OpenSubmit server
            action    - What should be done with this file
            timeout   - What is the timeout for running this job
            validator - URL of the validator script

    '''
    try:
        result = urlopen("%s/jobs/secret=%s"%(config.get("Server","url"),config.get("Server","secret")))
        fname=config.get("Execution","directory")+datetime.now().isoformat()
        headers=result.info()
        if headers['Action'] == 'get_config':
            # The server does not know us, so it demands registration before hand.
            logger.info("Machine unknown on server, perform registration first.")
            return [None]*5
        submid=headers['SubmissionFileId']
        action=headers['Action']
        timeout=int(headers['Timeout'])
        logger.info("Retrieved submission file %s for '%s' action: %s"%(submid, action, fname))
        if 'PostRunValidation' in headers:
            validator=headers['PostRunValidation']
        else:
            validator=None
        target=open(fname,"wb")
        target.write(result.read())
        target.close()
        return fname, submid, action, timeout, validator
    except HTTPError as e:
        if e.code == 404:
            logger.debug("Nothing to do.")
            return [None]*5
        else:
            logger.error(str(e))
            return [None]*5

def _unpack_job(config, fname, submid, action):
    '''
        Decompress the downloaded file "fname" into the globally defined "targetdir".
        Returns on success, or terminates the executor after notifying the OpenSubmit server
        about the problem.

        Returns None on error, or path were the compressed data now lives
    '''
    # os.chroot is not working with tarfile support
    finalpath=config.get("Execution","directory")+str(submid)+"/"
    shutil.rmtree(finalpath, ignore_errors=True)
    os.makedirs(finalpath)
    if zipfile.is_zipfile(fname):
        logger.debug("Valid ZIP file")
        f=zipfile.ZipFile(fname, 'r')
        logger.debug("Extracting ZIP file.")
        f.extractall(finalpath)
        os.remove(fname)
    elif tarfile.is_tarfile(fname):
        logger.debug("Valid TAR file")
        tar = tarfile.open(fname)
        logger.debug("Extracting TAR file.")
        tar.extractall(finalpath)
        tar.close()
        os.remove(fname)
    else:
        os.remove(fname)
        _send_result(config, "This is not a valid compressed file.",-1, submid, action)
        shutil.rmtree(finalpath, ignore_errors=True)
        return None
    dircontent=os.listdir(finalpath)
    logger.debug("Content after decompression: "+str(dircontent))
    if len(dircontent)==0:
        _send_result(config, "Your compressed upload is empty - no files in there.",-1, submid, action)
    elif len(dircontent)==1 and os.path.isdir(finalpath+os.sep+dircontent[0]):
        logger.warning("The archive contains no Makefile on top level and only the directory %s. I assume I should go in there ..."%(dircontent[0]))
        finalpath=finalpath+os.sep+dircontent[0]
    return finalpath

def _handle_alarm(signum, frame):
    '''
        Signal handler for timeout implementation
    '''
    # Needed for compatibility with both MacOS X and Linux
    if 'self' in frame.f_locals:
        pid=frame.f_locals['self'].pid
    else:
        pid=frame.f_back.f_locals['self'].pid
    logger.info("Got alarm signal, killing %s due to timeout."%(str(pid)))
    os.killpg(pid, signal.SIGTERM)

def _run_job(config, finalpath, cmd, submid, action, timeout, ignore_errors=False):
    '''
        Perform some execution activity with timeout support.
        This is used both for compilation and validator script execution.

        Return stdout of the job execution and a boolean flag of the execution was successfull
    '''
    logger.debug("Changing to target directory.")
    logger.debug("Installing signal handler for timeout")
    signal.signal(signal.SIGALRM, _handle_alarm)
    logger.info("Spawning process for "+str(cmd))
    try:
        proc=subprocess.Popen(cmd, cwd=finalpath, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, preexec_fn=os.setsid)
        logger.debug("Starting timeout counter: %u seconds"%timeout)
        signal.alarm(timeout)
        output=None
        stderr=None
        try:
            output, stderr = proc.communicate()
            logger.debug("Process terminated")
        except:
            logger.debug("Seems like the process got killed by the timeout handler")
        if output == None:
            output = ""
        else:
            output=output.decode("utf-8")
        if stderr == None:
            stderr = ""
        else:
            stderr=stderr.decode("utf-8")
        signal.alarm(0)
        if action=='test_compile':
            action_title='Compilation'
        elif action=='test_validity':
            action_title='Validation'
        elif action=='test_full':
            action_title='Testing'
        else:
            assert(False)
    except:
        if ignore_errors:
            return "", True             # act like nothing had happened
        else:
            logger.info("Exception on process execution: "+str(e))
            shutil.rmtree(finalpath, ignore_errors=True)
            return "", False
    if proc.returncode == 0:
        logger.info("Executed with error code 0: \n\n"+output)
        return output, True
    elif (proc.returncode == 0-signal.SIGTERM) or (proc.returncode == None):
        _send_result(config, "%s was terminated since it took too long (%u seconds). Output so far:\n\n%s"%(action_title,timeout,output), proc.returncode, submid, action)
        shutil.rmtree(finalpath, ignore_errors=True)
        return output, False
    else:
        dircontent = subprocess.check_output(["ls","-ln"])
        dircontent = dircontent.decode("utf-8")
        output=output+"\n\nDirectory content as I see it:\n\n"+dircontent
        _send_result(config, "%s was not successful:\n\n%s"%(action_title,output), proc.returncode, submid, action)
        shutil.rmtree(finalpath, ignore_errors=True)
        return output, False

def _kill_deadlocked_jobs(config):
    '''
        Terminate everything under the current user account that has run too long.
        This is a final safeguard if the SIGALRM stuff is not working.
        You better have no production servers running also under the current user account ...
    '''
    import psutil 
    ourpid=os.getpid()
    username=psutil.Process(ourpid).username
    # check for other processes running under this account
    for proc in psutil.process_iter():
        if proc.username == username and proc.pid != ourpid:
            runtime=time.time()-proc.create_time
            logger.debug("This user already runs %u for %u seconds."%(proc.pid,runtime))
            if runtime > int(config.get("Execution","timeout")):
                logger.debug("Killing %u due to exceeded runtime."%proc.pid)
                proc.kill()

def _can_run(config):
    '''
        Determines if the executor is configured to run fetched jobs one after the other.
        If this is the case, then check if another script instance is still running.
    '''
    if config.getboolean("Execution","serialize"):
        fp = open(config.get("Execution","pidfile"), 'w')
        try:
            fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
            logger.debug("Got the script lock")
        except IOError:
            logger.debug("Script is already running.")
            return False
    return True

def send_config(config_file):
    '''
        Sends the registration of this machine to the OpenSubmit web server.
    '''
    config = read_config(config_file)
    conf = os.uname()
    output = []
    output.append(["Operating system","%s %s (%s)"%(conf[0], conf[2], conf[4])])
    output.append(["CPUID information", _infos_cmd("cpuid")])
    output.append(["CC information", _infos_cmd("cc -v")])
    output.append(["JDK information", _infos_cmd("java -version")])
    output.append(["MPI information", _infos_cmd("mpirun -version")])
    output.append(["Scala information", _infos_cmd("scala -version")])
    output.append(["OpenCL headers", _infos_cmd("find /usr/include|grep opencl.h")])
    output.append(["OpenCL libraries", _infos_cmd("find /usr/lib/ -iname '*opencl*'")])
    output.append(["NVidia SMI", _infos_cmd("nvidia-smi -q")])
    output.append(["OpenCL Details", _infos_opencl()])
    logger.debug("Sending config data: "+str(output))
    post_data = [('Config',json.dumps(output)),('Name',_infos_cmd("hostname"))]
    post_data = urlencode(post_data)
    post_data = post_data.encode('utf-8')
    urlopen('%s/machines/secret=%s'%(config.get("Server","url"), config.get("Server","secret")), post_data)

def run(config_file):
    '''
        The primary worker function of the executor, fetches and runs jobs from the OpenSubmit server.
        Expects an existing registration of this machine.
    '''
    config = read_config(config_file)
    _kill_deadlocked_jobs(config)
    if _can_run(config):
        # fetch any available job
        fname, submid, action, timeout, validator=_fetch_job(config)
        if not fname:
            return False
        # decompress download, only returns on success
        finalpath=_unpack_job(config, fname, submid, action)
        if not finalpath:
            return False
        # perform action defined by the server for this download
        if action == 'test_compile':
            # run configure script, if available.
            output, success = _run_job(config, finalpath,['./configure'],submid, action, timeout, True)
            if not success:
                return False
            # build it, only returns on success
            output, success = _run_job(config, finalpath,['make'],submid, action, timeout)
            if not success:
                return False
            _send_result(config, output, 0, submid, action)
            shutil.rmtree(finalpath, ignore_errors=True)
            return True
        elif action == 'test_validity' or action == 'test_full':
            # prepare the output file for validator performance results
            perfdata_fname = finalpath+"/perfresults.csv" 
            open(perfdata_fname,"w").close()
            # run configure script, if available.
            output, success = _run_job(config, finalpath,['./configure'],submid, action, timeout, True)
            if not success:
                return False
            # build it
            output, success = _run_job(config, finalpath,['make'],submid,action,timeout)
            if not success:
                return False
            # fetch validator into target directory 
            logger.debug("Fetching validator script from "+validator)
            urllib.request.urlretrieve(validator, finalpath+"/download")
            if zipfile.is_zipfile(finalpath+"/download"):
                logger.debug("Validator is a ZIP file, unpacking it.")
                f=zipfile.ZipFile(finalpath+"/download", 'r')
                f.extractall(finalpath)
                os.remove(finalpath+"/download")
                # ZIP file is expected to contain 'validator.py'
                if not os.path.exists(finalpath+"/validator.py"):
                    logger.error("Validator ZIP package does not contain validator.py")
                    #TODO: Ugly hack, make error reporting better
                    _send_result(config, "Internal error, please consult the course administrators.", -1, submid, action, "")
            else:
                logger.debug("Validator is a single file, renaming it.")
                os.rename(finalpath+"/download",finalpath+"/validator.py")
            os.chmod(finalpath+"/validator.py", stat.S_IXUSR|stat.S_IRUSR)
            # Allow submission to load their own libraries
            logger.debug("Setting LD_LIBRARY_PATH to "+finalpath)
            os.environ['LD_LIBRARY_PATH']=finalpath
            # execute validator
            output, success = _run_job(config, finalpath,[config.get("Execution","script_runner"), 'validator.py', perfdata_fname],submid,action,timeout)
            if not success:
                return False
            perfdata= open(perfdata_fname,"r").read()
            _send_result(config, output, 0, submid, action, perfdata)
            shutil.rmtree(finalpath, ignore_errors=True)
            return True
        else:
            # unknown action, programming error in the server
            logger.error("Uknown action keyword from server: "+action)
            return False

if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "register":
        send_config(sys.argv[2])
    elif len(sys.argv) > 2 and sys.argv[1] == "run":
        run(sys.argv[2])
    else:
        print("python -m opensubmit.executor [register|run] executor.ini")
