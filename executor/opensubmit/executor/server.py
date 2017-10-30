'''
   Common functions related to communication with the OpenSubmit server.
'''

import logging
logger = logging.getLogger('opensubmit.executor')

import os, shutil, json
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

from .submission import Submission
from .result import Result
from .filesystem import create_working_dir
from .hostinfo import all_host_infos, ipaddress

def _send(config, urlpath, post_data):
    '''
    Send POST data to OpenSubmit server.
    '''
    server = config.get("Server","url")
    if server:
        post_data = urlencode(post_data)
        post_data = post_data.encode("utf-8",errors="ignore")
        url=server+urlpath
        urlopen(url, post_data)
    else:
        logger.info("Testing mode, not sending this result:\n{0}".format(str(post_data)))

def _fetch(url, target_dir, fname):
    '''
    Fetch data from an URL.
    '''
    logger.debug("Fetching from "+url)

    fullpath=target_dir+os.sep+fname

    tmpfile, headers = urllib.request.urlretrieve(url)
    if os.path.exists(fullpath):
        os.remove(fullpath)
    shutil.move(tmpfile, fullpath)

def send_result(sub:Submission, result:Result):
    '''
    Send validation result for Submission to OpenSubmit server.
    '''
    post_data = [("SubmissionFileId",sub.submission_file_id),
                ("Message", result.info_student.encode("utf-8",errors="ignore")),
                ("ErrorCode", result.error_code),
                ("Action", sub.action),
                ("PerfData", result.perf_data),
                ("Secret", sub._config.get("Server","secret")),
                ("UUID", sub._config.get("Server","uuid"))
                ]

    _send(sub._config, "/jobs/", post_data)

def send_hostinfo(config):
    '''
    Register this machine on OpenSubmit server by sending information.
    '''
    info = all_host_infos()
    logger.debug("Sending host information: "+str(info))
    post_data = [   ("Config",json.dumps(info)),
                ("UUID",config.get("Server","uuid")),
                ("Address",ipaddress()),
                ("Secret",config.get("Server","secret"))
            ]           

    _send(config, "/machines/", post_data)


def fetch_support_files(sub):
    '''
        Fetch support files for the job and unpack them in the submission
        working directory.
    '''
    if sub.support_files:
        _fetch(sub.support_files, sub.working_dir, 'download.support')
        unpack_if_needed(sub.working_dir, sub.working_dir+os.sep+'download.support')

def fetch_job(config):
    '''
        Fetch any available work from the OpenSubmit server,
        creates an according submission object and unpacks all student data.

        Returns a new Submission object or None if no work is available.

        Jobs are described by HTTP header entries in the response.
    '''
    sub=Submission(config)
    url="%s/jobs/?Secret=%s&UUID=%s"%( config.get("Server","url"),
                                       config.get("Server","secret"),
                                       config.get("Server","uuid"))
    try:
        result = urlopen(url)
        headers = result.info()
        if headers["Action"] == "get_config":
            # The server does not know us, so it demands registration before hand.
            logger.info("Machine unknown on server, sending registration first ...")
            send_hostinfo(config)
        sub.submission_file_id=headers["SubmissionFileId"]
        sub.submission_id=headers["SubmissionId"]
        sub.action=headers["Action"]
        sub.compile_on=(headers["Compile"]=='True')
        sub.timeout=int(headers["Timeout"])
        if "PostRunValidation" in headers:
            sub.validator = headers["PostRunValidation"]
        else:
            sub.validator = None
        if "SupportFiles" in headers:
            sub.support_files = headers["SupportFiles"]
        else:
            sub.support_files = None
        logger.debug("Got job: "+str(sub))
        # Store download file in working directory for validation
        sub.working_dir = create_working_dir(config, sub.submission_id)
        sub.download_file = sub.working_dir+os.sep+'download' 
        with open(sub.download_file,'wb') as target:
            target.write(result.read())
        return sub
    except HTTPError as e:
        if e.code == 404:
            logger.debug("Nothing to do.")
            return None
    except URLError as e:
        logger.error("Error while contacting {0}: {1}".format(url, str(e)))
        return None
