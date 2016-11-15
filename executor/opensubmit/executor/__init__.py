'''
    Everything that is about to be executed on a test machine.
'''

from urllib import urlencode
from urllib2 import urlopen, HTTPError, URLError
import logging, json
import zipfile, tarfile
import tempfile, os, platform, shutil, subprocess, signal, stat, sys, pickle, ConfigParser
import time
from threading import Timer
from datetime import datetime, timedelta
from lockfile import FileLock

logger=logging.getLogger("OpenSubmitExecutor")

# Expected in validator ZIP packages
VALIDATOR_FNAME = "validator.py"

# Configuration defaults, if option is not given.
# This is mainly intended for backward-ompatbility to older INI files.
defaults = {("Execution", "cleanup"): True,
            ("Execution", "message_size"): 10000,
            ("Execution", "compile_cmd"): "make"
           }
      

def read_config(config_file):
    '''
        Fill config dictionary, already check and interpret some values.
    '''
    config = ConfigParser.RawConfigParser()
    config.readfp(open(config_file))

    if not logger.handlers:
        # Before doing anything else, configure logging
        # Handlers might be already registered in repeated test suite runs
        # In production, this should never happen
        if config.getboolean("Logging", "to_file"):
            handler = logging.FileHandler(config.get("Logging", "file"))
        else:
            handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(config.get("Logging", "format")))
        logger.addHandler(handler)
    logger.setLevel(config.get("Logging", "level"))

    # set defaults for non-existing options
    for key, value in defaults.iteritems():
        if not config.has_option(key[0], key[1]):
            logger.debug("%s option not in INI file, assuming %s"%(str(key), str(value)))
            config.set(key[0], key[1], value)

    # sanity check for directory specification
    targetdir=config.get("Execution", "directory")
    if platform.system() is not "Windows":
        assert(targetdir.startswith("/")) # need a work around here 
    assert(targetdir.endswith(os.sep))
    return config

def _acquire_lock(config):
    '''
        Determines if the executor is configured to run fetched jobs one after the other.
        If this is the case, then check if another script instance is still running.
    '''
    if config.getboolean("Execution", "serialize"):
        lock = FileLock(config.get("Execution", "pidfile")) 
        try: 
            if lock.is_locked() and not lock.i_am_locking():
               logger.debug("Already locked")
               return False
            else:
               lock.acquire()
               logger.debug("Got the script lock")
        except Exception as e:
            logger.error("ERROR locking. " + str(e))           
            return False
    return True

def _cleanup_lock(config):
    '''
        Release locks, if set.
    '''
    if config.getboolean("Execution", "serialize"):
        lock = FileLock(config.get("Execution","pidfile"))
        logger.debug("Releasing lock")
        lock.release()

def _cleanup_files(config, finalpath):
    '''
        Remove all created while evaluating the submission
    '''
    if config.getboolean("Execution", "cleanup") == True:
        logger.info("Removing downloads at " + finalpath)
        shutil.rmtree(finalpath, ignore_errors=True) #fails often on windows
    else:
        logger.info("Keeping data for debugging: " + finalpath)

def _send_result(config, msg, error_code, submission_file_id, action, perfdata=None):
    '''
        Send some result to the OpenSubmit web server.
    '''
    message_size = config.getint("Execution","message_size")
    if message_size>0 and len(msg)>message_size:
        # We need to truncate excessive console output,
        # since this goes into the database.
        msg=msg[1:message_size]
        msg+="\n[Output truncated]"
    if not perfdata:
        perfdata=""
    logger.info("Test for submission file %s completed with error code %s: %s"%(submission_file_id, str(error_code), msg))
    # There are cases where the program was not finished, but we still deliver a result
    # Transmitting "None" is a bad idea, so we use a special code instead
    if error_code==None:
        error_code=-9999
    try:
    # Prepare response HTTP package
        post_data = [("SubmissionFileId",submission_file_id),
                    ("Message",msg.encode("utf-8",errors="ignore")),
                    ("ErrorCode",error_code),
                    ("Action",action),
                    ("PerfData",perfdata),
                    ("Secret",config.get("Server","secret")),
                    ("UUID",config.get("Server","uuid"))
                    ]
    
        post_data = urlencode(post_data)
        post_data = post_data.encode("utf-8",errors="ignore")
        urlopen("%s/jobs/"%config.get("Server","url"), post_data)
    except Exception as e:
        logging.error("ERROR send_result: " + str(e))

def _infos_host():
    ''' 
        Determine our own IP adress. This seems to be far more complicated than you would think:
    '''
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("gmail.com",80))
        result = s.getsockname()[0]
        s.close()
        return result
    except Exception as e:
        return ""

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
                infoset = [key for key in dir(device) if not key.startswith("__") and key not in ["extensions", "name"]]
                for attr in infoset:
                    try:
                        result.append("        %s: %s"%(attr.strip(), getattr(device, attr).strip()))
                    except:
                        pass
        return "\n".join(result)
    except Exception as e:
        return ""

def _infos_cmd(cmd, stdhndl=" 2>&1", e_shell=True):
    '''
        Determine some system information based on a shell command.
    '''
    try: #make it more portable, because cl.exe has no information mode 
        p = subprocess.Popen(cmd + stdhndl, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=e_shell)
        p.wait()
        out = "".join([p.stdout.read(),p.stderr.read()]).decode("utf-8",errors="ignore")
        if p.returncode!=0:
            out=""
        return out
    except Exception as e:
        return ""



def _unpack_if_needed(destination_path, fpath):
    '''
        Generic helper to unpack potential archives from the OpenSubmit server.
        Archives are automatically unpacked, regardless of the type. Single files are left as is
        and just moved to to the destination path.

        destination_path is a directory.
        fpath is a full-qualified path to some potential archive file.

        Returns directory content after being done, or None.
    '''

    # Perform un-archiving, in case
    if zipfile.is_zipfile(fpath):
        logger.debug("Detected ZIP file at %s, unpacking it."%(fpath))
        try:
            with zipfile.ZipFile(fpath, "r") as zip:
                zip.extractall(destination_path)
        except Exception as e:
            logger.error("ERROR extracting ZIP file: " + str(e))
            return None
    elif tarfile.is_tarfile(fpath):
        logger.debug("Detected TAR file at %s, unpacking it."%(fpath))
        try:
            with tarfile.open(fpath) as tar:
                tar.extractall(destination_path)
        except Exception as e:
            logger.error("ERROR extracting TAR file: " + str(e))
            return None
    else:
        if not fpath.startswith(destination_path):
            logger.debug("File at %s is a single non-archive file, copying it to %s"%(fpath, destination_path))
            try:
                shutil.copy(fpath, destination_path)
            except Exception as e:
                logger.error("Could not copy file: "+str(e))
                return None

    dircontent = os.listdir(destination_path)
    logger.debug("Content of %s is now: %s"%(destination_path,str(dircontent)))
    return dircontent


def _fetch_and_unpack(url, destination_path, download_filename, check_file=None):
    '''
        Generic helper to download files from the OpenSubmit server.

        Archives are automatically unpacked, regardless of the type. Single files are left as is.

        Callers must provided the intended unqualified name for the downloaded file, which is not deleted
        by this method. The file is stored in the destination_path directory, too.

        Callers can ask to check for the existence of some unqualified file name in the
        destination_path after download (and potential unarchiving) are done.

        Returns boolean success indicator.
    '''
    logger.debug("Fetching from "+url)
    download_fullqual = destination_path + download_filename

    # Perform download
    try:
        download_stream = urlopen(url)
        if os.path.exists(download_fullqual):
            os.remove(download_fullqual)
        with open(download_fullqual,"wb") as target:
            target.write(download_stream.read())
    except Exception as e:
        logger.error("ERROR while fetching from " + url + " " + str(e))
        return False

    if _unpack_if_needed(destination_path, download_fullqual):
        # Perform existence check
        if check_file:
            abspath_check_file = destination_path + check_file
            if not os.path.exists(abspath_check_file):
                logger.error("ERROR: Could not find expected file %s in %s after download / unarchiving.", check_file, destination_path)
                return False
        return True
    else:
        return False


def _fetch_validator(url, path):
        '''
            Fetch validator script (archive) from the given URL and store it under the given target path.

            Returns success indication as boolean value.
        '''
        logger.debug("Fetching validator script...")
        if _fetch_and_unpack(url, path, VALIDATOR_FNAME, VALIDATOR_FNAME):
            try:
                os.chmod(path+VALIDATOR_FNAME, stat.S_IXUSR|stat.S_IRUSR)
            except Exception as e:
                logger.error("ERROR setting file system attributes on %s: %s "%(VALIDATOR_FNAME, str(e)))
                return False
            return True


def _fetch_support_files(url, path):
        '''
            Fetch support files archive from the given URL and put it under the given target path.

            Returns success indication as boolean value.
        '''
        logger.debug("Fetching support files ... ")
        return _fetch_and_unpack(url, path, 'support.download')


def _create_temp_directory(config, submid):
    '''
        Create a fresh temporary directory for this submission.
        Returns the new path or None.
    '''
    # Fetch base directory from executor configuration
    basepath = config.get("Execution","directory")
    try:
        #use a new temp dir for each run, to skip problems with file locks on Windows
        finalpath = tempfile.mkdtemp(prefix=str(submid)+'_', dir=basepath)
    except Exception as e:
        logger.error("ERROR could not create temp dir: " + str(e))
        return None

    if not finalpath.endswith(os.sep):
        finalpath += os.sep

    logger.debug("New temporary directory %s for this submission.", finalpath)

    return finalpath

def _fetch_job(config):
    '''
        Fetch any available work from the OpenSubmit server.

        Jobs are described by HTTP header entries in the response.
        The download here contains the student data only.

        Returns job information as function result tuple:
            fname     - Fully qualified temporary file name for the job file
            submid    - ID of this file on the OpenSubmit server
            action    - What should be done with this file
            timeout   - What is the timeout for running this job
            validator - URL of the validator script
            support   - URL of the support files
            compile_on - Status of the compilation test flag in the assignment configuration
    '''
    try:
        result = urlopen("%s/jobs/?Secret=%s&UUID=%s"%(  config.get("Server","url"),
                                                        config.get("Server","secret"),
                                                        config.get("Server","uuid")))
        fname = config.get("Execution","directory")+datetime.now().isoformat().replace(":","")
        headers = result.info()
        if headers["Action"] == "get_config":
            # The server does not know us, so it demands registration before hand.
            logger.info("Machine unknown on server, perform 'opensubmit-exec configure' first.")
            return [None]*7
        submfileid = headers["SubmissionFileId"]
        submid = headers["SubmissionId"]
        action = headers["Action"]
        compile_on = (headers["Compile"]=='True')
        timeout = int(headers["Timeout"])
        logger.info("Retrieved submission file %s from submission %s for '%s' action: %s" % (submfileid, submid, action, fname))
        if "PostRunValidation" in headers:
            validator = headers["PostRunValidation"]
        else:
            validator = None
        if "SupportFiles" in headers:
            support = headers["SupportFiles"]
        else:
            support = None
        with open(fname,"wb") as target:
            target.write(result.read())
        #logger.debug(str((fname, submid, action, timeout, validator, support, compile_on)))
        return fname, submfileid, action, timeout, validator, support, compile_on
    except HTTPError as e:
        if e.code == 404:
            logger.debug("Nothing to do.")
            return [None]*7
        else:
            logger.error("ERROR HTTP return code: " + str(e))
            return [None]*7
    except URLError as e:
        logger.error("ERROR could not contact OpenSubmit web server at %s (%s)"%(config.get("Server","url"), str(e)))
        return [None]*7
    except Exception as e:
        logger.error("ERROR unknown: " + str(e))
        return [None]*7

def _handle_alarm(proc):
    '''
        Signal handler for timeout implementation
    '''
    # Needed for compatibility with both MacOS X, Linux and Windows
    logger.info("Got alarm signal, killing %d due to timeout." % proc.pid)
    try:
        if platform.system() == "Windows":
            proc.terminate()
        else:
            os.killpg(proc.pid, signal.SIGTERM) #not available on Windows proc.terminate kills not the whole process group!
    except Exception as e:
        logger.error("ERROR killing process: %d" % proc.pid)

def _run_job(config, finalpath, cmd, submid, action, timeout, ignore_errors=False):
    '''
        Perform some execution activity with timeout support.
        This is used both for compilation and validator script execution.

        Return stdout of the job execution and a boolean flag of the execution was successfull
    '''
    dircontent = os.listdir(finalpath)
    logger.debug("Content before start: " + str(dircontent))
    logger.debug("Installing signal handler for timeout")
    logger.info("Spawning process for " + str(cmd))
    
    try:
        if platform.system() == "Windows":
            proc = subprocess.Popen(cmd, cwd=finalpath, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        else:
            proc = subprocess.Popen(cmd, cwd=finalpath, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, preexec_fn=os.setsid)
        logger.debug("Starting timeout counter: %u seconds" % timeout)
        timer = Timer(timeout, _handle_alarm, args = [proc])
        timer.start()
        output = None
        stderr = None
        
        try:
            output, stderr = proc.communicate()
            logger.debug("Process terminated")
        except Exception as e:
            logger.debug("Seems like the process got killed by the timeout handler: " + str(e))
        
        if output == None:
            output = ""
        else:
            output = output.decode("utf-8",errors="ignore")
            
        if stderr == None:
            stderr = ""
        else:
            stderr = stderr.decode("utf-8",errors="ignore")
        
        try:
            logger.debug("Cancel timeout")
            timer.cancel()
        except Exception as e:
            logger.error("ERROR cancel timeout " + str(e))
        
        if action == "test_compile":
            action_title = "Compilation"
        elif action == "test_validity":
            action_title = "Validation"
        elif action == "test_full":
            action_title = "Testing"
        else:
            assert(False)
    except:
        if ignore_errors:
            return "", True             # act like nothing had happened
        else:
            logger.info("Exception on process execution: " + str(sys.exc_info()))
            _cleanup_files(config, finalpath)
            return "", False
    
    if proc.returncode == 0:
        logger.info("Executed with error code 0: \n\n" + output)
        return output, True
    elif (proc.returncode == 0-signal.SIGTERM) or (proc.returncode == None):
        _send_result(config, "%s was terminated since it took too long (%u seconds). Output so far:\n\n%s"%(action_title,timeout,output), proc.returncode, submid, action)
        _cleanup_files(config, finalpath)
        return output, False
    else:
        try:
            dircontent = subprocess.check_output(["cmd.exe","/c","dir", "/b", finalpath]) if platform.system()=="Windows" else subprocess.check_output(["ls","-ln",finalpath])
        except Exception as e:
            logger.error("ERROR getting directory content. " + str(e))
            dircontent = "Not available."
        dircontent = dircontent.decode("utf-8",errors="ignore")
        output = output + "\n\nDirectory content as I see it:\n\n" + dircontent
        _send_result(config, "%s was not successful:\n\n%s"%(action_title,output), proc.returncode, submid, action)
        _cleanup_files(config, finalpath)
        return output, False

def _kill_deadlocked_jobs(config):
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

def send_config(config_file):
    '''
        Sends the registration of this machine to the OpenSubmit web server.
    '''
    config = read_config(config_file)
    conf = platform.uname()
    output = []
    output.append(["Operating system","%s %s %s (%s)"%(conf[0], conf[2], conf[3], conf[4])])
    try:
       from cpuinfo import cpuinfo
       cpu=cpuinfo.get_cpu_info()
       conf="%s, %s, %s Family %d Model %d Stepping %d #%d" % (cpu["brand"],cpu["vendor_id"],cpu["arch"],cpu['family'],cpu['model'],cpu['stepping'],cpu["count"])
    except:
       conf=platform.processor() #may be empty on Linux because of partial implemtation in platform
       
    output.append(["CPUID information", conf])
     
    if platform.system()=="Windows":
       conf = _infos_cmd("cl.exe|@echo off","") #force returncode 0
       conf = conf.split("\n")[0] #extract version info
    else:
       conf = _infos_cmd("cc -v")
   
    output.append(["CC information", conf ])
    output.append(["JDK information", _infos_cmd("java -version")])
    output.append(["MPI information", _infos_cmd("mpirun -version")])
    output.append(["Scala information", _infos_cmd("scala -version")])
    output.append(["OpenCL headers", _infos_cmd("find /usr/include|grep opencl.h")])
    output.append(["OpenCL libraries", _infos_cmd("find /usr/lib/ -iname '*opencl*'")])
    output.append(["NVidia SMI", _infos_cmd("nvidia-smi -q")])
    output.append(["OpenCL Details", _infos_opencl()])
    try:
        logger.debug("Sending config data: "+str(output))
        post_data = [   ("Config",json.dumps(output)),
                    ("UUID",config.get("Server","uuid")),
                    ("Address",_infos_host()),
                    ("Secret",config.get("Server","secret"))
                ]           
            
        post_data = urlencode(post_data)
        post_data = post_data.encode("utf-8",errors="ignore")
    
        urlopen("%s/machines/"% config.get("Server","url"), post_data)
    except Exception as e:
        logger.error("ERROR Could not contact OpenSubmit web server at %s (%s)" % (config.get("Server","url"), str(e)))

def run(config_file):
    '''
        The primary worker function of the executor, fetches and runs jobs from the OpenSubmit server.
        Expects an existing registration of this machine.

        Returns boolean that indicates success.
    '''
    config = read_config(config_file)
    compile_cmd = config.get("Execution","compile_cmd")
    _kill_deadlocked_jobs(config)

    if _acquire_lock(config):
        # fetch any available job information
        fname, submid, action, timeout, validator_url, support_url, compile_on = _fetch_job(config)
        if not fname:
            logger.debug("Nothing to do")
            _cleanup_lock(config)
            return False

        # At this stage, we have a downloaded student archive and several additional job informations

        # Create fresh temporary directory
        targetdir = _create_temp_directory(config, submid)

        # Unpack student data, some validity checks
        dircontent = _unpack_if_needed(targetdir, fname)
        if len(dircontent) == 0:
            _send_result(config, "Your compressed upload is empty - no files in there.",-1, submid, action) # never returns
            logger.debug("Student archive is empty, notification about this stored as validation result.")
            _cleanup_lock(config)
            return False
        elif len(dircontent) == 1 and os.path.isdir(targetdir + dircontent[0] + os.sep):
            logger.warning("The student archive contains no Makefile on top level and only the directory %s. I assume I should go in there ..." % (dircontent[0]))
            targetdir = targetdir + dircontent[0] + os.sep

        # Download and decompress support files, if given
        # We do this after the student files uncompressing, so that they cannot overwrite the tutor files
        if support_url:
            _fetch_support_files(support_url, targetdir)

        # perform action defined by the server for this download
        if action == "test_compile":
            # run configure script, if available.
            output, success = _run_job(config, targetdir,["./configure"],submid, action, timeout, True)
            if not success:
                logger.debug("Configure failed")
                _cleanup_lock(config)
                return False
            # build it, only returns on success
            output, success = _run_job(config, targetdir, compile_cmd.split(" "), submid, action, timeout)
            if not success:
                logger.debug("Compilation failed")
                _cleanup_lock(config)
                return False
            _send_result(config, output, 0, submid, action)
            _cleanup_files(config, targetdir)
            logger.debug("Compilation worked")
            _cleanup_lock(config)
            return True
        elif action == "test_validity" or action == "test_full":
            # prepare the output file for validator performance results
            perfdata_fname = targetdir+"perfresults.csv"
            open(perfdata_fname,"w").close()
            if compile_on:
                # run configure script, if available.
                output, success = _run_job(config, targetdir,["./configure"],submid, action, timeout, True)
                if not success:
                    logger.debug("Configure failed")
                    _cleanup_lock(config)
                    return False
                # build it
                output, success = _run_job(config, targetdir,compile_cmd.split(" "),submid,action,timeout)
                if not success:
                    logger.debug("Job execution failed")
                    _cleanup_lock(config)
                    return False
            # fetch validator into target directory
            if not _fetch_validator(validator_url, targetdir):
                logger.debug("Validator fetching failed, cancelling task")
                _cleanup_lock(config)
                return False
            # Allow submission to load their own libraries
            logger.debug("Setting LD_LIBRARY_PATH to "+targetdir)
            os.environ["LD_LIBRARY_PATH"]=targetdir
            # execute validator
            output, success = _run_job(config, targetdir,[config.get("Execution","script_runner"), targetdir+VALIDATOR_FNAME, perfdata_fname],submid,action,timeout)
            if not success:
                logger.debug("Job execution failed")
                _cleanup_lock(config)
                return False
            perfdata= open(perfdata_fname,"r").read()
            _send_result(config, output, 0, submid, action, perfdata)
            _cleanup_files(config, targetdir)
            logger.debug("Validty test worked")
            _cleanup_lock(config)
            return True
        else:
            # unknown action, programming error in the server
            logger.error("Unknown action keyword %s from server"%(action,))
            _cleanup_lock(config)
            return False
        
if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "register":
        send_config(sys.argv[2])
    elif len(sys.argv) > 2 and sys.argv[1] == "run":
        run(sys.argv[2])
    else:
        print("python -m opensubmit.executor [register|run] executor.ini")
    print "Exit"