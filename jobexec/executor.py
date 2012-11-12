#!/usr/bin/env python
import urllib, urllib2, logging, zipfile, tarfile, tempfile, os, shutil, subprocess, signal
from datetime import datetime

# BEGIN Configuration
FORMAT = "%(asctime)-15s (%(levelname)s): %(message)s"
logging.basicConfig(format=FORMAT, level=logging.INFO, filename='/tmp/executor.log')
submit_server = "http://localhost:8000"
secret = "49845zut93purfh977TTTiuhgalkjfnk89"		
#targetdir=tempfile.mkdtemp()+"/"
targetdir="/tmp/"		# with trailing slash
max_time=5				# maximum execution time in seconds
# END Configuration

def send_result(msg, error_code, submission_file_id, action):
	logging.info("Test for submission file %s completed with error code %s: %s"%(submission_file_id, str(error_code), msg))
	post_data = [('SubmissionFileId',submission_file_id),('Message',msg),('ErrorCode',error_code),('Action',action)]    
	try:
		urllib2.urlopen('%s/jobs/secret=%s'%(submit_server, secret), urllib.urlencode(post_data))	
	except urllib2.HTTPError, e:
		logging.error(str(e))
		exit(-1)

def fetch_job():
	try:
		result = urllib2.urlopen("%s/jobs/secret=%s"%(submit_server,secret))
		fname=targetdir+datetime.now().isoformat()
		submid=result.info()['SubmissionFileId']
		action=result.info()['Action']
		logging.info("Retrieved submission file %s for '%s' action: %s"%(submid, action, fname))
		target=open(fname,"wb")
		target.write(result.read())
		target.close()
		return fname, submid, action
	except urllib2.HTTPError, e:
		if e.code == 404:
			logging.debug("Nothing to do.")
			exit(0)
		else:
			logging.error(str(e))
			exit(-1)

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

def handle_alarm(signum, frame):
	logging.info("Got alarm signal, killing due to timeout.")
	if 'self' in frame.f_locals:
		pid=frame.f_locals['self'].pid
	else:
		pid=frame.f_back.f_locals['self'].pid
	os.killpg(pid, signal.SIGTERM)

def run_job(finalpath, cmd, submid, action, keepdata=False):
	logging.debug("Changing to target directory.")
	os.chdir(finalpath)
	logging.debug("Installing signal handler for timeout")
	signal.signal(signal.SIGALRM, handle_alarm)
	logging.info("Spawning process for "+str(cmd))
	proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, preexec_fn=os.setsid)
	logging.debug("Starting timeout counter")
	signal.alarm(max_time)
	output, stderr = proc.communicate()
	logging.debug("Process is done")
	signal.alarm(0)
	logging.debug("Cleaning up temporary data")
	if proc.returncode == 0:
		logging.info("Executed with error code 0: \n\n"+output)
		if not keepdata:
			shutil.rmtree(finalpath, ignore_errors=True)
		return output
	elif proc.returncode == 0-signal.SIGTERM:
		shutil.rmtree(finalpath, ignore_errors=True)
		send_result("'%s' call was terminated since it took too long (%u seconds). Output so far:\n\n%s"%(' '.join(cmd),max_time,output), proc.returncode, submid, action)
		exit(-1)		
	else:
		shutil.rmtree(finalpath, ignore_errors=True)
		send_result("'%s' call was not successful:\n\n%s"%(str(cmd[0]),output), proc.returncode, submid, action)
		exit(-1)		

fname, submid, action=fetch_job()
finalpath=unpack_job(fname, submid, action)
if action == 'compile':
	output=run_job(finalpath,['make'],submid, action)
	send_result(output, 0, submid, action)
elif action == 'run':
	run_job(finalpath,['make'],submid,action,keepdata=True)
	output=run_job(finalpath,['make','run'],submid,action)
	send_result(output, 0, submid, action)
else:
	assert(False)
