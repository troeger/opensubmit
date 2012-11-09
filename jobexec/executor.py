import urllib, urllib2, logging, zipfile, tarfile, tempfile, os, shutil, subprocess, signal
from datetime import datetime

# BEGIN Configuration
logging.basicConfig(level=logging.DEBUG)
submit_server = "http://localhost:8000"
secret = "39845zut93purfh977TTTiuhgalkjfnk89"		
#targetdir=tempfile.mkdtemp()+"/"
targetdir="/tmp/"		# with trailing slash
max_time=5				# maximum execution time in seconds
# END Configuration

def send_result(msg, error_code, submission_file_id):
	logging.info("Test for submission file %s completed with error code %s: %s"%(submission_file_id, str(error_code), msg))
	post_data = [('SubmissionFileId',submission_file_id),('Message',msg),('ErrorCode',error_code)]    
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
		logging.info("Retrieved submission file %s: %s"%(submid, fname))
		target=open(fname,"wb")
		target.write(result.read())
		target.close()
		return fname, submid
	except urllib2.HTTPError, e:
		if e.code == 404:
			logging.info("Nothing to do.")
			exit(0)
		else:
			logging.error(str(e))
			exit(-1)

def unpack_job(fname, submid):
	# os.chroot is not working with tarfile support
	finalpath=targetdir+str(submid)+"/"
	shutil.rmtree(finalpath, ignore_errors=True)
	os.makedirs(finalpath)
	if zipfile.is_zipfile(fname):
		logging.info("Valid ZIP file")
		f=zipfile.ZipFile(fname, 'r')
		f.extractall(finalpath)
		return finalpath
	elif tarfile.is_tarfile(fname):
		logging.info("Valid TAR file")
		tar = tarfile.open(fname)
		logging.info("Extracting TAR file.")
		tar.extractall(finalpath)
		tar.close()
		return finalpath
	else:
		send_result("This is not a valid compressed file.",-1, submid)
		exit(-1)		

def handle_alarm(signum, frame):
	logging.info("Got alarm signal, killing due to timeout.")
	frame.f_back.f_locals['self'].terminate()

def run_job(finalpath, cmd, submid):
	logging.info("Changing to target directory.")
	os.chdir(finalpath)
	logging.info("Installing signal handler for timeout")
	signal.signal(signal.SIGALRM, handle_alarm)
	logging.info("Spawning process for "+str(cmd))
	proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	logging.info("Starting timeout counter")
	signal.alarm(max_time)
	proc.wait()
	signal.alarm(0)
	output=proc.stdout.read()
	if proc.returncode == 0:
		logging.info("Success: \n\n"+output)
		return output
	elif proc.returncode == 0-signal.SIGTERM:
		send_result("'%s' call was terminated since it took too long (%u seconds). Output so far:\n\n%s"%(str(cmd[0]),max_time,output), proc.returncode, submid)
		exit(-1)		
	else:
		send_result("'%s' call was not successful:\n\n%s"%(str(cmd[0]),output), proc.returncode, submid)
		exit(-1)		

fname, submid=fetch_job()
finalpath=unpack_job(fname, submid)
run_job(finalpath,['make'],submid)
output=run_job(finalpath,['make','run'],submid)
send_result(output, 0, submid)

