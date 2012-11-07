import urllib, urllib2, logging, zipfile
from datetime import datetime

# BEGIN Configuration
logging.basicConfig(level=logging.DEBUG)
submit_server = "http://localhost:8000"
secret = "39845zut93purfh977TTTiuhgalkjfnk89"		
target_dir = "/tmp/"
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
		fname=target_dir+datetime.now().isoformat()
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
	logging.info("Unpacking "+fname)
	if not zipfile.is_zipfile(fname):
		send_result("This is not a valid ZIP file.",-1, submid)
		exit(-1)
	logging.info("Valid ZIP file")

fname, submid=fetch_job()
testdir=unpack_job(fname, submid)
