'''
Helper functions to deal with the OpenSubmit server and its downloads.
'''

import logging
logger = logging.getLogger('opensubmitexec')

import shutil
import os
import glob
import json

from urllib.request import urlopen, urlretrieve
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

from .hostinfo import all_host_infos, ipaddress
from .job import Job
from .filesystem import create_working_dir, unpack_if_needed

def fetch(url, fullpath):
    '''
    Fetch data from an URL and save it under the given target name.
    '''
    logger.debug("Fetching %s from %s"%(fullpath, url))

    tmpfile, headers = urlretrieve(url)
    if os.path.exists(fullpath):
        os.remove(fullpath)
    shutil.move(tmpfile, fullpath)


def send(config, urlpath, post_data):
    '''
    Send POST data to an OpenSubmit server url path, according to the configuration.
    '''
    server = config.get("Server","url")
    post_data = urlencode(post_data)
    post_data = post_data.encode("utf-8",errors="ignore")
    url=server+urlpath
    try:
        urlopen(url, post_data)
    except Exception as e:
        logger.error('Error while sending data to server: '+str(e))

def send_hostinfo(config):
    '''
    Register this host on OpenSubmit test machine.
    '''
    info = all_host_infos()
    logger.debug("Sending host information: "+str(info))
    post_data = [("Config",json.dumps(info)),
                 ("UUID",config.get("Server","uuid")),
                 ("Address",ipaddress()),
                 ("Secret",config.get("Server","secret"))
                ]           

    send(config, "/machines/", post_data)

def fetch_job(config):
    '''
    Fetch any available work from the OpenSubmit server and
    return an according job object, or None.
    '''
    url="%s/jobs/?Secret=%s&UUID=%s"%( config.get("Server","url"),
                                       config.get("Server","secret"),
                                       config.get("Server","uuid"))

    try:
        # Fetch information from server
        result = urlopen(url)
        headers = result.info()
        if headers["Action"] == "get_config":
            # The server does not know us, so it demands registration before hand.
            logger.info("Machine unknown on server, sending registration ...")
            send_hostinfo(config)
            return None

        # Create job object with information we got
        job=Job(config)
        job.file_id=headers["SubmissionFileId"]
        job.sub_id=headers["SubmissionId"]
        if "Timeout" in headers:
            job.timeout=int(headers["Timeout"])
        if "PostRunValidation" in headers:
            job.validator_url = headers["PostRunValidation"]
        job.working_dir  = create_working_dir(config, job.sub_id)

        # Store submission in working directory 
        submission_fname = job.working_dir + 'download.student'
        with open(submission_fname,'wb') as target:
            target.write(result.read())
        assert(os.path.exists(submission_fname))

        # Unpack student submission first, so that teacher files overwrite
        numfiles = unpack_if_needed(job.working_dir, submission_fname)
        dircontent = os.listdir(job.working_dir)

        # Check what we got from the student
        if numfiles is 0:
            logger.error("Submission archive file has no content.")
            job.send_result(FailResult("Your compressed upload is empty - no files in there."))
            return None
        elif numfiles == 1 and os.path.isdir(job.working_dir + dircontent[0] + os.sep):
                logger.warning("The student archive contains only the directory %s. I assume I should go in there ..." % (dircontent[0]))
                job.working_dir = job.working_dir + dircontent[0] + os.sep

        # Store validator package in working directory
        validator_fname  = job.working_dir + 'download.validator'
        fetch(job.validator_url, validator_fname)

        # Unpack validator package
        unpack_if_needed(job.working_dir, validator_fname)
        if not os.path.exists(job.validator_script_name):
            # The download is already the script
            shutil.move(validator_fname, job.validator_script_name)

        logger.debug("Got job: "+str(job))

        return job
    except HTTPError as e:
        if e.code == 404:
            logger.debug("Nothing to do.")
            return None
    except URLError as e:
        logger.error("Error while contacting {0}: {1}".format(url, str(e)))
        return None

def fake_fetch_job(config, src_dir):
    '''
    Act like fetch_job, but take the validator file and the student
    submission files directly from a directory.

    Intended for testing purposes when developing test scripts.

    Check also cmdline.py.
    '''
    job = Job(config, online=False)
    job.working_dir = create_working_dir(config, '42')
    for fname in glob.glob(src_dir+os.sep+'*'):
        logger.debug("Copying {0} to {1} ...".format(fname, job.working_dir))
        shutil.copy(fname, job.working_dir)
    logger.debug("Got fake job: "+str(job))

    return job
