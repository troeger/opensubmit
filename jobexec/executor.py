import urllib, urllib2, logging, zipfile, tarfile, tempfile, os, shutil
from datetime import datetime

# BEGIN Configuration
logging.basicConfig(level=logging.DEBUG)
submit_server = "http://localhost:8000"
secret = "39845zut93purfh977TTTiuhgalkjfnk89"		
#targetdir=tempfile.mkdtemp()+"/"
targetdir="/tmp/jobexec/"
# END Configuration

def send_result(msg, error_code, submission_file_id):
	logging.info("Test for submission %s completed with error code %s: %s"%(submission_file_id, str(error_code), msg))
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

def unpack_run_job(fname, submid, targetdir):
	# os.chroot is not working with tarfile support
	if zipfile.is_zipfile(fname):
		logging.info("Valid ZIP file")
	if tarfile.is_tarfile(fname):
		logging.info("Valid TAR file")
		tar = tarfile.open(fname)
		tar.extractall(targetdir)
		tar.close()
	logging.info("Invalid compressed file")
#	send_result("This is not a valid compressed file.",-1, submid)
	exit(-1)

fname, submid=fetch_job()
unpack_run_job(fname, submid, targetdir)
