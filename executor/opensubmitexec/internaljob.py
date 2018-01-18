import os.path
import sys
import importlib

from .config import read_config
from .exceptions import *
from .server import send_post
from .filesystem import remove_working_directory

import logging
logger = logging.getLogger('opensubmitexec')

UNSPECIFIC_ERROR = -9999


class InternalJob():
    """Internal base class for jobs,
       with additional private functions."""

    # The current executor configuration.
    _config = None
    # Talk to the configured OpenSubmit server?
    _online = None
    # Action requested by the server (legacy)
    action = None

    submission_url = None
    validator_url = None
    result_sent = False

    # The base name of the validation / full test script
    # on disk, for importing.
    _validator_import_name = 'validator'

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

        try:
            module = importlib.import_module(self._validator_import_name)
        except Exception as e:
            text_student = "Internal validation problem, please contact your course responsible."
            text_tutor = "Exception while loading the validator: " + str(e)
            self._send_result(text_student, text_tutor, UNSPECIFIC_ERROR)
            return

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
                text_student = "Internal problem while validating your submission. Please contact the course responsible."
                text_tutor = "Unknown exception while running the validator: {0}".format(
                    str(e))
            # We got the text. Report the problem.
            self._send_result(text_student, text_tutor, UNSPECIFIC_ERROR)
            return
        # no unhandled exception during the execution of the validator
        if not self.result_sent:
            logger.debug("Validation script forgot result sending, assuming success.")
            self.send_pass_result()
        # roll back
        sys.path = old_path
        # Test script was executed, result was somehow sent
        # Clean the file system, since we can't do anything else
        remove_working_directory(self.working_dir, self._config)

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
