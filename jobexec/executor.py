#!/usr/bin/env python
import urllib, urllib2, logging, zipfile, tarfile, tempfile, os, shutil, subprocess, signal, stat, ConfigParser
from datetime import datetime

submit_server = None
secret = None		
targetdir=None

# Send some result to the SUBMIT server
def send_result(msg, error_code, submission_file_id, action):
	logging.info("Test for submission file %s completed with error code %s: %s"%(submission_file_id, str(error_code), msg))
	post_data = [('SubmissionFileId',submission_file_id),('Message',msg),('ErrorCode',error_code),('Action',action)]    
	try:
		urllib2.urlopen('%s/jobs/secret=%s'%(submit_server, secret), urllib.urlencode(post_data))	
	except urllib2.HTTPError, e:
		logging.error(str(e))
		exit(-1)

# Fetch any available work from the SUBMIT server
# returns job information from the server
def fetch_job():
	try:
		result = urllib2.urlopen("%s/jobs/secret=%s"%(submit_server,secret))
		fname=targetdir+datetime.now().isoformat()
		headers=result.info()
		submid=headers['SubmissionFileId']
		action=headers['Action']
		timeout=int(headers['Timeout'])
		logging.info("Retrieved submission file %s for '%s' action: %s"%(submid, action, fname))
		if 'PostRunValidation' in headers:
			validator=headers['PostRunValidation']
			logging.debug("Using validator from "+validator)
		else:
			validator=None
		target=open(fname,"wb")
		target.write(result.read())
		target.close()
		return fname, submid, action, timeout, validator
	except urllib2.HTTPError, e:
		if e.code == 404:
			logging.debug("Nothing to do.")
			exit(0)
		else:
			logging.error(str(e))
			exit(-1)

# Decompress the downloaded file into "targetdir"
# Returns on success, or terminates the executor after notifying the SUBMIT server
def unpack_job(fname, submid, action):
	# os.chroot is not working with tarfile support
	finalpath=targetdir+str(submid)+"/"
	shutil.rmtree(finalpath, ignore_errors=True)
	os.makedirs(finalpath)
	if zipfile.is_zipfile(fname):
		logging.debug("Valid ZIP file")
		f=zipfile.ZipFile(fname, 'r')
		f.extractall(finalpath)
		os.remove(fname)
		return finalpath
	elif tarfile.is_tarfile(fname):
		logging.debug("Valid TAR file")
		tar = tarfile.open(fname)
		logging.debug("Extracting TAR file.")
		tar.extractall(finalpath)
		tar.close()
		os.remove(fname)
		return finalpath
	else:
		os.remove(fname)
		shutil.rmtree(finalpath, ignore_errors=True)
		send_result("This is not a valid compressed file.",-1, submid, action)
		exit(-1)		

# Signal handler for timeout implementation
def handle_alarm(signum, frame):
	logging.info("Got alarm signal, killing due to timeout.")
	# Needed for compatibility with both MacOS X and Linux
	if 'self' in frame.f_locals:
		pid=frame.f_locals['self'].pid
	else:
		pid=frame.f_back.f_locals['self'].pid
	os.killpg(pid, signal.SIGTERM)

# Perform some execution activity, with timeout support
# This is used both for compilation and validator script execution
def run_job(finalpath, cmd, submid, action, timeout, keepdata=False):
	logging.debug("Changing to target directory.")
	os.chdir(finalpath)
	logging.debug("Installing signal handler for timeout")
	signal.signal(signal.SIGALRM, handle_alarm)
	logging.info("Spawning process for "+str(cmd))
	proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, preexec_fn=os.setsid)
	logging.debug("Starting timeout counter")
	signal.alarm(timeout)
	output, stderr = proc.communicate()
	logging.debug("Process is done")
	signal.alarm(0)
	logging.debug("Cleaning up temporary data")
	if action=='test_compile':
		action_title='Compilation'
	elif action=='test_validity':
		action_title='Validation'
	elif action=='test_full':
		action_title='Testing'
	else:
		assert(False)
	if proc.returncode == 0:
		logging.info("Executed with error code 0: \n\n"+output)
		if not keepdata:
			shutil.rmtree(finalpath, ignore_errors=True)
		return output
	elif proc.returncode == 0-signal.SIGTERM:
		shutil.rmtree(finalpath, ignore_errors=True)
		send_result("%s was terminated since it took too long (%u seconds). Output so far:\n\n%s"%(action_title,timeout,output), proc.returncode, submid, action)
		exit(-1)		
	else:
		dircontent = subprocess.check_output(["ls","-ln"])
		output=output+"\n\nDirectory content as I see it:\n\n"+dircontent
		shutil.rmtree(finalpath, ignore_errors=True)
		send_result("%s was not successful:\n\n%s"%(action_title,output), proc.returncode, submid, action)
		exit(-1)		

# read configuration
config = ConfigParser.RawConfigParser()
config.read("executor.cfg")
# configure logging module
logformat=config.get("Logging","format")
logfile=config.get("Logging","file")
loglevel=logging._levelNames[config.get("Logging","level")]
logtofile=config.getboolean("Logging","to_file")
if logtofile:
	logging.basicConfig(format=logformat, level=loglevel, filename='/tmp/executor.log')
else:
	logging.basicConfig(format=logformat, level=loglevel)	
# set global variables
submit_server=config.get("Server","url")
secret=config.get("Server","secret")
targetdir=config.get("Execution","directory")
assert(targetdir.startswith('/'))
assert(targetdir.endswith('/'))
script_runner=config.get("Execution","script_runner")

# fetch any available job
fname, submid, action, timeout, validator=fetch_job()
# decompress download, only returns on success
finalpath=unpack_job(fname, submid, action)
# perform action defined by the server for this download
if action == 'test_compile':
	# build it, only returns on success
	output=run_job(finalpath,['make'],submid, action, timeout)
	send_result(output, 0, submid, action)
elif action == 'test_validity' or action == 'test_full':
	# build it, only returns on success
	run_job(finalpath,['make'],submid,action,timeout,keepdata=True)
	# fetch validator into target directory 
	logging.debug("Fetching validator script from "+validator)
	urllib.urlretrieve(validator, finalpath+"validator.py")
	os.chmod(finalpath+"validator.py", stat.S_IXUSR|stat.S_IRUSR)
	# execute validator
	output=run_job(finalpath,[script_runner, 'validator.py'],submid,action,timeout)
	send_result(output, 0, submid, action)
else:
	# unknown action, programming error in the server
	assert(False)
