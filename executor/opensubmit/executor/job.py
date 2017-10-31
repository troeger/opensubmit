import logging
logger = logging.getLogger('opensubmit.executor')

import os, shutil, json, sys, subprocess, platform, stat
from urllib.request import urlopen, urlretrieve
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

from .submission import Submission
from .filesystem import create_working_dir, unpack_if_needed, has_file
from .hostinfo import all_host_infos, ipaddress
from .execution import shell_execution
from .result import Result, PassResult, FailResult

class Job():
    submission:Submission=None      # The submission object describing the meta-data

    submission_url:str=None         # Download source for the student file / archive
    support_url:str=None            # Download source for the support files archive
    validator_url:str=None          # Download source for the validator script (archive)

    working_dir:str = None          # The working directory for this job

    timeout:int=None                # The timeout for execution, as reported by the server
    action:str=None                 # Activity to be performed (legacy)
    compile_on:bool=None            # Flag defining if this is a compilation job

    def __str__(self):
        return str(vars(self))

    @property
    def submission_files(self):
        return self.working_dir + 'download.student'

    @property
    def support_files(self):
        return self.working_dir + 'download.support'

    @property
    def validator_files(self):
        return self.working_dir + 'download.validator'

    @property
    def validator_script(self):
        return self.working_dir + 'validator.py'

    @property
    def perfdata_file(self):
        return self.working_dir + 'perfresults.csv'


    def _fetch(self, url, fullpath):
        '''
        Fetch data from an URL and save it under the given target name.
        '''
        logger.debug("Fetching %s from %s"%(fullpath, url))

        tmpfile, headers = urlretrieve(url)
        if os.path.exists(fullpath):
            os.remove(fullpath)
        shutil.move(tmpfile, fullpath)

    def fetch_support_files(self):
        if self.support_url:
            self._fetch(self.support_url, self.support_files)
            unpack_if_needed(self.working_dir, self.support_files)
        return True

    def fetch_validator_files(self):
        if self.validator_url:
            self._fetch(self.validator_url, self.validator_files)
            unpack_if_needed(self.working_dir, self.validator_files)
            if not os.path.exists(self.validator_script):
                # The download is already the script
                shutil.move(self.validator_files, self.validator_script)
            try:
                os.chmod(self.validator_script, stat.S_IXUSR|stat.S_IRUSR)
            except Exception as e:
                logger.error("Could not adjust file system attributes on %s: %s "%(self.validator_files, str(e)))
                return False
        return True
    

    def prepare(self) -> Result:
        '''
        Prepare working directory for job execution.     
        Return FailResult (to be returned to server) or PassResult to indicate the possiblity
        for further process. 
        '''
        # Unpack student archive
        numfiles = unpack_if_needed(self.working_dir, self.submission_files)
        # Check number and kind of files in archive
        if numfiles is 0:
            logger.debug("Student archive is empty, notification about this stored as validation result.")
            return FailResult("Your compressed upload is empty - no files in there.")
        elif numfiles == 1 and os.path.isdir(self.working_dir + dircontent[0] + os.sep):
            logger.warning("The student archive contains only the directory %s. I assume I should go in there ..." % (dircontent[0]))
            self.working_dir = self.working_dir + dircontent[0] + os.sep
        if not self.fetch_validator_files():
            return FailResult("Internal error while fetching the validator.")
        if not self.fetch_support_files():
            return FailResult("Internal error while fetching the support files.")
        return PassResult()


    def compile(self):
        ''' Perform compilation activity.
        '''
        if has_file(self.working_dir, 'configure'):
            logger.info("Running configure")
            result = shell_execution(['configure'], self.working_dir, self.timeout)
            if not result.is_ok():
                return result
        compile_cmd = self.submission._config.get("Execution","compile_cmd")
        logger.info("Running compilation with "+compile_cmd)
        return shell_execution(compile_cmd, self.working_dir, self.timeout)

    def run(self) -> Result:
        '''
        Perform some execution activity with timeout support.
        Returns Result object.
        '''
        dircontent = os.listdir(self.working_dir)
        logger.debug("Working directory before start: " + str(dircontent))

        if self.action == 'test_compile':
            logger.debug('This is a compile job')
            return self.compile()
        elif self.action == "test_validity" or self.action == "test_full":
            logger.debug('This is a validation job')
            logger.debug("Running compilation before validation")
            compile_result = self.compile()
            if compile_result.is_ok():
                cmdline=[   self.submission._config.get("Execution","script_runner"),
                            self.validator_script,
                            self.perfdata_file]
                logger.debug("Running validator: "+str(cmdline))
                return shell_execution(cmdline, self.working_dir, self.timeout)
            else:
                logger.debug('Compilation failed, not running validation.')
                return compile_result

    def send_result(self, result:Result):
        '''
        Send validation result for Submission to OpenSubmit server.
        '''
        result.info_student = result.stdout     # legacy approach
        post_data = [("SubmissionFileId",self.submission.file_id),
                    ("Message", result.info_student),
                    ("ErrorCode", result.error_code),
                    ("Action", self.action),
                    ("PerfData", result.perf_data),
                    ("Secret", self.submission._config.get("Server","secret")),
                    ("UUID", self.submission._config.get("Server","uuid"))
                    ]
        logger.debug('Sending result to OpenSubmit Server: '+str(post_data))
        _send(self.submission._config, "/jobs/", post_data)


def _send(config, urlpath, post_data):
    '''
    Send POST data to OpenSubmit server.
    '''
    server = config.get("Server","url")
    post_data = urlencode(post_data)
    post_data = post_data.encode("utf-8",errors="ignore")
    url=server+urlpath
    urlopen(url, post_data)

def send_hostinfo(config):
    '''
    Register this machine on OpenSubmit server by sending information.
    '''
    info = all_host_infos()
    logger.debug("Sending host information: "+str(info))
    post_data = [("Config",json.dumps(info)),
                 ("UUID",config.get("Server","uuid")),
                 ("Address",ipaddress()),
                 ("Secret",config.get("Server","secret"))
                ]           

    _send(config, "/machines/", post_data)

def fetch_job(config):
    '''
    Fetch any available work from the OpenSubmit server and
    return an according job object, or None.
    '''
    job=Job()
    job.submission=Submission(config)
    url="%s/jobs/?Secret=%s&UUID=%s"%( config.get("Server","url"),
                                       config.get("Server","secret"),
                                       config.get("Server","uuid"))
    try:
        result = urlopen(url)
        headers = result.info()
        if headers["Action"] == "get_config":
            # The server does not know us, so it demands registration before hand.
            logger.info("Machine unknown on server, sending registration ...")
            send_hostinfo(config)
            return None
        job.submission.file_id=headers["SubmissionFileId"]
        job.submission.sub_id=headers["SubmissionId"]
        job.action=headers["Action"]
        job.compile_on=(headers["Compile"]=='True')
        if "Timeout" in headers:
            job.timeout=int(headers["Timeout"])
        if "PostRunValidation" in headers:
            job.validator_url = headers["PostRunValidation"]
        if "SupportFiles" in headers:
            job.support_url = headers["SupportFiles"]
        # Store student file in working directory 
        job.working_dir = create_working_dir(config, job.submission.sub_id)
        with open(job.submission_files,'wb') as target:
            target.write(result.read())
        logger.debug("Got job: "+str(job))
        return job
    except HTTPError as e:
        if e.code == 404:
            logger.debug("Nothing to do.")
            return None
    except URLError as e:
        logger.error("Error while contacting {0}: {1}".format(url, str(e)))
        return None