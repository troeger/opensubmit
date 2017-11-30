'''
The official executor API for validation test and full test scripts.
'''

import os
import sys
import importlib
import shutil
import os.path
import glob
import json

from .compiler import compiler_cmdline, GCC
from .config import read_config
from .running import kill_longrunning, RunningProgram
from .exceptions import *
from .filesystem import has_file, create_working_dir, prepare_working_directory
from .hostinfo import all_host_infos, ipaddress

from urllib.request import urlopen, urlretrieve
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

import logging
logger = logging.getLogger('opensubmitexec')

UNSPECIFIC_ERROR = -9999


class Job():
    '''
    A OpenSubmit job to be run by the test machine.
    '''

    # The current executor configuration.
    _config = None
    # Talk to the configured OpenSubmit server?
    _online = None

    # Download source for the student sub
    submission_url = None
    # Download source for the validator
    validator_url = None
    # The working directory for this job
    working_dir = None
    # The timeout for execution, as demanded by the server
    timeout = None
    # The OpenSubmit submission ID
    submission_id = None
    # The OpenSubmit submission file ID
    file_id = None
    # Did the validator script sent a result to the server?
    result_sent = False
    # Action requested by the server (legacy)
    action = None
    # Name of the submitting student
    submitter_name = None
    # Student ID of the submitting student
    submitter_student_id = None
    # Names of the submission authors
    author_names = None
    # Name of the study program of the submitter
    submitter_studyprogram = None
    # Name of the course where this submission was done
    course = None
    # Name of the assignment where this job was done
    assignment = None

    # The base name of the validation / full test script
    # on disk, for importing.
    _validator_import_name = 'validator'

    @property
    # The file name of the validation / full test script
    # on disk, after unpacking / renaming.
    def validator_script_name(self):
        return self.working_dir + self._validator_import_name + '.py'

    def __init__(self, config=None, online=True):
        if config:
            self._config = config
        else:
            self._config = read_config()
        self._online = online

    def __str__(self):
        '''
        Nicer logging of job objects.
        '''
        return str(vars(self))

    def _run_validate(self):
        '''
        Execute the validate() method in the test script belonging to this job.
        '''
        assert(os.path.exists(self.validator_script_name))
        old_path = sys.path
        sys.path = [self.working_dir] + old_path
        # logger.debug('Python search path is now {0}.'.format(sys.path))
        module = importlib.import_module(self._validator_import_name)

        # Looped validator loading in the test suite demands this
        importlib.reload(module)

        # make the call
        try:
            module.validate(self)
        except Exception as e:
            # get more info
            text_student = None
            text_tutor = None
            if type(e) is TerminationException:
                text_student = "The execution of '{0}' terminated unexpectely.".format(
                    e.instance.name)
                text_tutor = "The execution of '{0}' terminated unexpectely.".format(
                    e.instance.name)
                text_student += "\n\nOutput so far:\n" + e.output
                text_tutor += "\n\nOutput so far:\n" + e.output
            elif type(e) is TimeoutException:
                text_student = "The execution of '{0}' was cancelled, since it took too long.".format(
                    e.instance.name)
                text_tutor = "The execution of '{0}' was cancelled due to timeout.".format(
                    e.instance.name)
                text_student += "\n\nOutput so far:\n" + e.output
                text_tutor += "\n\nOutput so far:\n" + e.output
            elif type(e) is NestedException:
                text_student = "Unexpected problem during the execution of '{0}'. {1}".format(
                    e.instance.name,
                    str(e.real_exception))
                text_tutor = "Unkown exception during the execution of '{0}'. {1}".format(
                    e.instance.name,
                    str(e.real_exception))
                text_student += "\n\nOutput so far:\n" + e.output
                text_tutor += "\n\nOutput so far:\n" + e.output
            elif type(e) is WrongExitStatusException:
                text_student = "The execution of '{0}' resulted in the unexpected exit status {1}.".format(
                    e.instance.name,
                    e.got)
                text_tutor = "The execution of '{0}' resulted in the unexpected exit status {1}.".format(
                    e.instance.name,
                    e.got)
                text_student += "\n\nOutput so far:\n" + e.output
                text_tutor += "\n\nOutput so far:\n" + e.output
            elif type(e) is JobException:
                # Some problem with our own code
                text_student = e.info_student
                text_tutor = e.info_tutor
            elif type(e) is FileNotFoundError:
                text_student = "A file is missing: {0}".format(
                    str(e))
                text_tutor = "Missing file: {0}".format(
                    str(e))
            elif type(e) is AssertionError:
                # Need this harsh approach to kill the
                # test suite execution at this point
                # Otherwise, the problem gets lost in
                # the log storm
                logger.error(
                    "Failed assertion in validation script. Should not happen in production.")
                exit(-1)
            else:
                # Something really unexpected
                text_student = "Internal problem while validating your submission. {0}".format(
                    str(e))
                text_tutor = "Unknown exception while running the validator. {0}".format(
                    str(e))
            # We got the text. Report the problem.
            self._send_result(text_student, text_tutor, UNSPECIFIC_ERROR)
            return
        # no unhandled exception during the execution of the validator
        if not self.result_sent:
            logger.debug("Validation script forgot result sending.")
            self.send_pass_result()
        # roll back
        sys.path = old_path

    def _send_result(self, info_student, info_tutor, error_code):
        post_data = [("SubmissionFileId", self.file_id),
                     ("Message", info_student),
                     ("Action", self.action),
                     ("MessageTutor", info_tutor),
                     ("ExecutorDir", self.working_dir),
                     ("ErrorCode", error_code),
                     ("Secret", self._config.get("Server", "secret")),
                     ("UUID", self._config.get("Server", "uuid"))
                     ]
        logger.info(
            'Sending result to OpenSubmit Server: ' + str(post_data))
        if self._online:
            send_post(self._config, "/jobs/", post_data)
        self.result_sent = True

    def send_fail_result(self, info_student, info_tutor):
        self._send_result(info_student, info_tutor, UNSPECIFIC_ERROR)

    def send_pass_result(self,
                         info_student="All tests passed. Awesome!",
                         info_tutor="All tests passed."):
        self._send_result(info_student, info_tutor, 0)

    def delete_binaries(self):
        '''
        Scans the submission files in the self.working_dir for
        binaries and deletes them.
        Returns the list of deleted files.
        '''
        raise NotImplementedError

    def run_configure(self, mandatory=True):
        '''
        Runs the configure tool configured for the machine in self.working_dir.
        '''
        if not has_file(self.working_dir, 'configure'):
            if mandatory:
                raise FileNotFoundError(
                    "Could not find a configure script for execution.")
            else:
                return
        try:
            prog = RunningProgram(self, 'configure')
            prog.expect_exit_status(0)
        except Exception:
            if mandatory:
                raise

    def run_make(self, mandatory=True):
        '''
        Runs the make tool configured for the machine in self.working_dir.
        '''
        if not has_file(self.working_dir, 'Makefile'):
            if mandatory:
                raise FileNotFoundError("Could not find a Makefile.")
            else:
                return
        try:
            prog = RunningProgram(self, 'make')
            prog.expect_exit_status(0)
        except Exception:
            if mandatory:
                raise

    def run_compiler(self, compiler=GCC, inputs=None, output=None):
        '''
        Runs the compiler in self.working_dir.
        '''
        # Let exceptions travel through
        prog = RunningProgram(self, *compiler_cmdline(compiler=compiler,
                                                      inputs=inputs,
                                                      output=output))
        prog.expect_exit_status(0)

    def run_build(self, compiler=GCC, inputs=None, output=None):
        logger.info("Running build steps ...")
        self.run_configure(mandatory=False)
        self.run_make(mandatory=False)
        self.run_compiler(compiler=compiler,
                          inputs=inputs,
                          output=output)

    def spawn_program(self, name, arguments=[], timeout=30, exclusive=False):
        '''
        Spawns a program in the working directory and allows
        interaction with it. Returns a RunningProgram object.

        The caller can demand exclusive execution on this machine.
        '''
        logger.debug("Spawning program for interaction ...")
        if exclusive:
            kill_longrunning(self.config)

        return RunningProgram(self, name, arguments, timeout)

    def run_program(self, name, arguments=[], timeout=30, exclusive=False):
        '''
        Runs a program in the working directory.
        The result is a tuple of exit code and output.

        The caller can demand exclusive execution on this machine.
        '''
        logger.debug("Running program ...")
        if exclusive:
            kill_longrunning(self.config)

        prog = RunningProgram(self, name, arguments, timeout)
        return prog.expect_end()

    def find_keywords(self, keywords, filepattern):
        '''
        Searches self.working_dir for files containing specific keywords.
        Expects a list of keywords to be searched for and the file pattern
        (*.c) as parameters.
        Returns the names of the files containing all of the keywords.
        '''
        raise NotImplementedError

    def ensure_files(self, filenames):
        '''
        Searches the student submission for specific files.
        Expects a list of filenames. Returns a boolean indicator.
        '''
        logger.debug("Testing {0} for the following files: {1}".format(
            self.working_dir, filenames))
        dircontent = os.listdir(self.working_dir)
        for fname in filenames:
            if fname not in dircontent:
                return False
        return True


def fetch(url, fullpath):
    '''
    Fetch data from an URL and save it under the given target name.
    '''
    logger.debug("Fetching %s from %s" % (fullpath, url))

    tmpfile, headers = urlretrieve(url)
    if os.path.exists(fullpath):
        os.remove(fullpath)
    shutil.move(tmpfile, fullpath)


def send_post(config, urlpath, post_data):
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
                 ("Action", "get_config"),
                 ("UUID", config.get("Server", "uuid")),
                 ("Address", ipaddress()),
                 ("Secret", config.get("Server", "secret"))
                 ]

    send_post(config, "/machines/", post_data)


def compatible_api_version(server_version):
    '''
    Check if this server API version is compatible to us.
    '''
    try:
        semver = server_version.split('.')
        if semver[0] != '1':
            logger.error('Server API version (%s) is too new for us. Please update the executor installation.'%server_version)
            return False
        else:
            return True
    except Exception:
        logger.error('Cannot understand the server API version (%s). Please update the executor installation.'%server_version)
        return False


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
        if not compatible_api_version(headers["APIVersion"]):
            return None

        if headers["Action"] == "get_config":
            # The server does not know us,
            # so it demands registration before hand.
            logger.info("Machine unknown on server, sending registration ...")
            send_hostinfo(config)
            return None

        # Create job object with information we got
        job = Job(config)

        job.submitter_name = headers['SubmitterName']
        job.author_names = headers['AuthorNames']
        job.submitter_studyprogram = headers['SubmitterStudyProgram']
        job.course = headers['Course']
        job.assignment = headers['Assignment']
        job.action = headers["Action"]
        job.file_id = headers["SubmissionFileId"]
        job.sub_id = headers["SubmissionId"]
        job.file_name = headers["SubmissionOriginalFilename"]
        job.submitter_student_id = headers["SubmitterStudentId"]
        if "Timeout" in headers:
            job.timeout = int(headers["Timeout"])
        if "PostRunValidation" in headers:
            job.validator_url = headers["PostRunValidation"]
        job.working_dir = create_working_dir(config, job.sub_id)

        # Store submission in working directory
        submission_fname = job.working_dir + job.file_name
        with open(submission_fname, 'wb') as target:
            target.write(result.read())
        assert(os.path.exists(submission_fname))

        # Store validator package in working directory
        validator_fname = job.working_dir + 'download.validator'
        fetch(job.validator_url, validator_fname)

        try:
            prepare_working_directory(job, submission_fname, validator_fname)
        except JobException:
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
    try:
        prepare_working_directory(job,
                                  submission_fname=submission,
                                  validator_fname=validator)
    except JobException:
        return None
    else:
        logger.debug("Got fake job: " + str(job))
        return job

