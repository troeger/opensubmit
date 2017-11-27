'''
Helper functions to deal with the OpenSubmit server and its downloads.
'''

import shutil
import os
import os.path
import glob
import json

from urllib.request import urlopen, urlretrieve
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

from .hostinfo import all_host_infos, ipaddress
from .job import Job
from .filesystem import create_working_dir, prepare_working_directory

import logging
logger = logging.getLogger('opensubmitexec')


def fetch(url, fullpath):
    '''
    Fetch data from an URL and save it under the given target name.
    '''
    logger.debug("Fetching %s from %s" % (fullpath, url))

    tmpfile, headers = urlretrieve(url)
    if os.path.exists(fullpath):
        os.remove(fullpath)
    shutil.move(tmpfile, fullpath)


def send(config, urlpath, post_data):
    '''
    Send POST data to an OpenSubmit server url path,
    according to the configuration.
    '''
    server = config.get("Server", "url")
    post_data = urlencode(post_data)
    post_data = post_data.encode("utf-8", errors="ignore")
    url = server + urlpath
    try:
        urlopen(url, post_data)
    except Exception as e:
        logger.error('Error while sending data to server: ' + str(e))


def send_hostinfo(config):
    '''
    Register this host on OpenSubmit test machine.
    '''
    info = all_host_infos()
    logger.debug("Sending host information: " + str(info))
    post_data = [("Config", json.dumps(info)),
                 ("UUID", config.get("Server", "uuid")),
                 ("Address", ipaddress()),
                 ("Secret", config.get("Server", "secret"))
                 ]

    send(config, "/machines/", post_data)


def fetch_job(config):
    '''
    Fetch any available work from the OpenSubmit server and
    return an according job object, or None.
    '''
    url = "%s/jobs/?Secret=%s&UUID=%s" % (config.get("Server", "url"),
                                          config.get("Server", "secret"),
                                          config.get("Server", "uuid"))

    try:
        # Fetch information from server
        result = urlopen(url)
        headers = result.info()
        if headers["Action"] == "get_config":
            # The server does not know us,
            # so it demands registration before hand.
            logger.info("Machine unknown on server, sending registration ...")
            send_hostinfo(config)
            return None

        # Create job object with information we got
        job = Job(config)
        job.file_id = headers["SubmissionFileId"]
        job.sub_id = headers["SubmissionId"]
        if "Timeout" in headers:
            job.timeout = int(headers["Timeout"])
        if "PostRunValidation" in headers:
            job.validator_url = headers["PostRunValidation"]
        job.working_dir = create_working_dir(config, job.sub_id)

        # Store submission in working directory
        submission_fname = job.working_dir + 'download.student'
        with open(submission_fname, 'wb') as target:
            target.write(result.read())
        assert(os.path.exists(submission_fname))

        # Store validator package in working directory
        validator_fname = job.working_dir + 'download.validator'
        fetch(job.validator_url, validator_fname)

        result = prepare_working_directory(job, submission_fname, validator_fname)
        if not result.is_ok():
            logger.error("Preparation of working directory failed.")
            return None
        else:
            logger.debug("Got job: " + str(job))
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
    logger.debug("Creating fake job from " + src_dir)
    job = Job(config, online=False)
    job.working_dir = create_working_dir(config, '42')
    case_files = glob.glob(src_dir + os.sep + '*')
    assert(len(case_files) == 2)
    logger.debug('Found ')
    for fname in glob.glob(src_dir + os.sep + '*'):
        logger.debug("Copying {0} to {1} ...".format(fname, job.working_dir))
        shutil.copy(fname, job.working_dir)
    if os.path.basename(case_files[0]) in ['validator.py', 'validator.zip']:
        validator = case_files[0]
        submission = case_files[1]
    else:
        validator = case_files[1]
        submission = case_files[0]
    logger.debug('{0} is the validator.'.format(validator))
    logger.debug('{0} the submission.'.format(submission))
    result = prepare_working_directory(job, submission_fname=submission, validator_fname=validator)
    if not result.is_ok():
        return None
    else:
        logger.debug("Got fake job: " + str(job))
        return job
