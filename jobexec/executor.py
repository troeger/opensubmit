"""
This is the executor script for the OpenSubmit system.
It is intended to run on a dedicated host, in order to download
and check student code.
"""

import urllib, urllib.request, urllib.error, urllib.parse
import logging, json
import zipfile, tarfile
import tempfile, os, shutil, subprocess, signal, stat, configparser, sys, fcntl, pickle
import time
try:
    import psutil       # compiled version for Py3 is crashing on MacOS X
    havePsUtil=True
except:
    havePsUtil=False
from datetime import datetime, timedelta

# Global configuration for the script, filled from the config file
submit_server = None
secret = None       
targetdir=None
pidfile=None

def cleanup_and_exit(finalpath, exit_code):
    ''' 
        Exit this script, clean any student code or generated
        data before.
    '''
    shutil.rmtree(finalpath, ignore_errors=True)
    exit(exit_code)

def send_result(msg, error_code, submission_file_id, action, perfdata=None):
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
    logging.info("Test for submission file %s completed with error code %s: %s"%(submission_file_id, str(error_code), msg))
    # There are cases where the program was not finished, but we still deliver a result
    # Transmitting "None" is a bad idea, so we use a special code instead
    if error_code==None:
        error_code=-9999    
    # Prepare response HTTP package
    post_data = [('SubmissionFileId',submission_file_id),('Message',msg),('ErrorCode',error_code),('Action',action),('PerfData',perfdata)]    
    try:
        post_data = urllib.parse.urlencode(post_data)
        post_data = post_data.encode('utf-8')
        urllib.request.urlopen('%s/jobs/secret=%s'%(submit_server, secret), post_data)  
    except urllib.error.HTTPError as e:
        logging.error(str(e))
        exit(-1)

def infos_opencl():
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

def infos_cmd(cmd):
    '''
        Determine some system information based on a shell command.
    '''
    try:
        out = subprocess.check_output(cmd+" 2>&1", shell=True)
        out = out.decode("utf-8")
        return out
    except:
        return ""

def send_config():
    '''
        Sends the configuration of this machine to the OpenSubmit web server.
    '''
    conf = os.uname()
    output = []
    output.append(["Operating system","%s %s (%s)"%(conf[0], conf[2], conf[4])])
    output.append(["CPUID information", infos_cmd("cpuid")])
    output.append(["CC information", infos_cmd("cc -v")])
    output.append(["JDK information", infos_cmd("java -version")])
    output.append(["MPI information", infos_cmd("mpirun -version")])
    output.append(["Scala information", infos_cmd("scala -version")])
    output.append(["OpenCL headers", infos_cmd("find /usr/include|grep opencl.h")])
    output.append(["OpenCL libraries", infos_cmd("find /usr/lib/ -iname '*opencl*'")])
    output.append(["NVidia SMI", infos_cmd("nvidia-smi -q")])
    output.append(["OpenCL Details", infos_opencl()])
    logging.debug("Sending config data: "+str(output))
    post_data = [('Config',json.dumps(output)),('Name',infos_cmd("hostname"))]
    post_data = urllib.parse.urlencode(post_data)
    post_data = post_data.encode('utf-8')
    urllib.request.urlopen('%s/machines/secret=%s'%(submit_server, secret), post_data)

def fetch_job():
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
        result = urllib.request.urlopen("%s/jobs/secret=%s"%(submit_server,secret))
        fname=targetdir+datetime.now().isoformat()
        headers=result.info()
        if headers['Action'] == 'get_config':
            # The server does not know us, so it demands registration before hand.
            print("Machine unknown on server, run 'executor.py register' first")
            exit(1)            
        submid=headers['SubmissionFileId']
        action=headers['Action']
        timeout=int(headers['Timeout'])
        logging.info("Retrieved submission file %s for '%s' action: %s"%(submid, action, fname))
        if 'PostRunValidation' in headers:
            validator=headers['PostRunValidation']
        else:
            validator=None
        target=open(fname,"wb")
        target.write(result.read())
        target.close()
        return fname, submid, action, timeout, validator
    except urllib.error.HTTPError as e:
        if e.code == 404:
            logging.debug("Nothing to do.")
            exit(0)
        else:
            logging.error(str(e))
            exit(-1)

def unpack_job(fname, submid, action):
    '''
        Decompress the downloaded file "fname" into the globally defined "targetdir".
        Returns on success, or terminates the executor after notifying the OpenSubmit server
        about the problem.
    '''
    # os.chroot is not working with tarfile support
    finalpath=targetdir+str(submid)+"/"
    shutil.rmtree(finalpath, ignore_errors=True)
    os.makedirs(finalpath)
    if zipfile.is_zipfile(fname):
        logging.debug("Valid ZIP file")
        f=zipfile.ZipFile(fname, 'r')
        logging.debug("Extracting ZIP file.")
        f.extractall(finalpath)
        os.remove(fname)
    elif tarfile.is_tarfile(fname):
        logging.debug("Valid TAR file")
        tar = tarfile.open(fname)
        logging.debug("Extracting TAR file.")
        tar.extractall(finalpath)
        tar.close()
        os.remove(fname)
    else:
        os.remove(fname)
        send_result("This is not a valid compressed file.",-1, submid, action)
        cleanup_and_exit(finalpath, -1)
    dircontent=os.listdir(finalpath)
    logging.debug("Content after decompression: "+str(dircontent))
    if len(dircontent)==0:
        send_result("Your compressed upload is empty - no files in there.",-1, submid, action)
    elif len(dircontent)==1 and os.path.isdir(finalpath+os.sep+dircontent[0]):
        logging.warning("The archive contains no Makefile on top level and only the directory %s. I assume I should go in there ..."%(dircontent[0]))
        finalpath=finalpath+os.sep+dircontent[0]
    return finalpath

def handle_alarm(signum, frame):
    '''
        Signal handler for timeout implementation
    '''
    # Needed for compatibility with both MacOS X and Linux
    if 'self' in frame.f_locals:
        pid=frame.f_locals['self'].pid
    else:
        pid=frame.f_back.f_locals['self'].pid
    logging.info("Got alarm signal, killing %s due to timeout."%(str(pid)))
    os.killpg(pid, signal.SIGTERM)

def run_job(finalpath, cmd, submid, action, timeout, ignore_errors=False):
    '''
        Perform some execution activity with timeout support.
        This is used both for compilation and validator script execution.
    '''
    logging.debug("Changing to target directory.")
    os.chdir(finalpath)
    logging.debug("Installing signal handler for timeout")
    signal.signal(signal.SIGALRM, handle_alarm)
    logging.info("Spawning process for "+str(cmd))
    try:
        proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, preexec_fn=os.setsid)
        logging.debug("Starting timeout counter: %u seconds"%timeout)
        signal.alarm(timeout)
        output=None
        stderr=None
        try:
            output, stderr = proc.communicate()
            logging.debug("Process terminated")
        except:
            logging.debug("Seems like the process got killed by the timeout handler")
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
            return ""
        else:
            logging.info("Exception on process execution: "+str(e))
            cleanup_and_exit(finalpath, -1) 
    if proc.returncode == 0:
        logging.info("Executed with error code 0: \n\n"+output)
        return output
    elif (proc.returncode == 0-signal.SIGTERM) or (proc.returncode == None):
        send_result("%s was terminated since it took too long (%u seconds). Output so far:\n\n%s"%(action_title,timeout,output), proc.returncode, submid, action)
        cleanup_and_exit(finalpath, -1)
    else:
        dircontent = subprocess.check_output(["ls","-ln"])
        dircontent = dircontent.decode("utf-8")
        output=output+"\n\nDirectory content as I see it:\n\n"+dircontent
        send_result("%s was not successful:\n\n%s"%(action_title,output), proc.returncode, submid, action)
        cleanup_and_exit(finalpath, -1)


'''
    Read configuration file, either as specified on command-line, or from
    the default location. Set global config variables accordingly.
'''
if len(sys.argv) < 3 or sys.argv[1] not in ["register","run"]:
    print("%s [register|run] <config_file>"%sys.argv[0])
    exit(-1)

config = configparser.RawConfigParser()
config.read(sys.argv[2])
logformat=config.get("Logging","format")
logfile=config.get("Logging","file")
loglevel=logging._levelNames[config.get("Logging","level")]
logtofile=config.getboolean("Logging","to_file")
if logtofile:
    logging.basicConfig(format=logformat, level=loglevel, filename='/tmp/executor.log')
else:
    logging.basicConfig(format=logformat, level=loglevel)   
# set global variables from config file
submit_server=config.get("Server","url")
secret=config.get("Server","secret")
targetdir=config.get("Execution","directory")
pidfile=config.get("Execution","pidfile")
maxruntime=int(config.get("Execution","timeout"))
assert(targetdir.startswith('/'))
assert(targetdir.endswith('/'))
script_runner=config.get("Execution","script_runner")
serialize=config.getboolean("Execution","serialize")

if sys.argv[1] == "register":
    # Determine machine configuration and send it
    send_config()
    exit(0)

if havePsUtil:
    # terminate everything under this account that runs too long
    # this is a final safeguard if the SIGALRM stuff is not working
    ourpid=os.getpid()
    username=psutil.Process(ourpid).username
    # check for other processes running under this account
    for proc in psutil.process_iter():
        if proc.username == username and proc.pid != ourpid:
            runtime=time.time()-proc.create_time
            logging.debug("This user already runs %u for %u seconds."%(proc.pid,runtime))
            if runtime > maxruntime:
                logging.debug("Killing %u due to exceeded runtime."%proc.pid)
                proc.kill()

# If the configuration says when need to serialize, check this
# long-runners may have being killed already before, together with their lock
if serialize:
    fp = open(pidfile, 'w')
    try:
        fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
        logging.debug("Got the script lock")
    except IOError:
        logging.debug("Script is already running.")
        exit(0)


# fetch any available job
fname, submid, action, timeout, validator=fetch_job()
# decompress download, only returns on success
finalpath=unpack_job(fname, submid, action)
# perform action defined by the server for this download
if action == 'test_compile':
    # run configure script, if available.
    #TODO: document this in the front-end
    run_job(finalpath,['./configure'],submid, action, timeout, True)
    # build it, only returns on success
    output=run_job(finalpath,['make'],submid, action, timeout)
    send_result(output, 0, submid, action)
    cleanup_and_exit(finalpath, 0)
elif action == 'test_validity' or action == 'test_full':
    # prepare the output file for validator performance results
    perfdata_fname = finalpath+"/perfresults.csv" 
    open(perfdata_fname,"w").close()
    # run configure script, if available.
    #TODO: document this in the front-end
    run_job(finalpath,['./configure'],submid, action, timeout, True)
    # build it, only returns on success
    run_job(finalpath,['make'],submid,action,timeout)
    # fetch validator into target directory 
    logging.debug("Fetching validator script from "+validator)
    urllib.request.urlretrieve(validator, finalpath+"/download")
    if zipfile.is_zipfile(finalpath+"/download"):
        logging.debug("Validator is a ZIP file, unpacking it.")
        f=zipfile.ZipFile(finalpath+"/download", 'r')
        f.extractall(finalpath)
        os.remove(finalpath+"/download")
        # ZIP file is expected to contain 'validator.py'
        if not os.path.exists(finalpath+"/validator.py"):
            logging.error("Validator ZIP package does not contain validator.py")
            #TODO: Ugly hack, make error reporting better
            send_result("Internal error, please consult the course administrators.", -1, submid, action, "")
    else:
        logging.debug("Validator is a single file, renaming it.")
        os.rename(finalpath+"/download",finalpath+"/validator.py")
    os.chmod(finalpath+"/validator.py", stat.S_IXUSR|stat.S_IRUSR)
    # Allow submission to load their own libraries
    logging.debug("Setting LD_LIBRARY_PATH to "+finalpath)
    os.environ['LD_LIBRARY_PATH']=finalpath
    # execute validator
    output=run_job(finalpath,[script_runner, 'validator.py', perfdata_fname],submid,action,timeout)
    perfdata= open(perfdata_fname,"r").read()
    send_result(output, 0, submid, action, perfdata)
    cleanup_and_exit(finalpath, 0)
else:
    # unknown action, programming error in the server
    assert(False)
