'''
The official executor API for validation test and full test scripts.
'''

import logging
logger = logging.getLogger('opensubmitexec')

import os, shutil, json, sys, subprocess, platform, stat, importlib

from .compiler import call_compiler, call_make, GCC
from .execution import shell_execution
from .result import Result, PassResult, FailResult, ExecutorBrokenResult
from .config import read_config
from . import server

class Job():
    _config = None                # The current executor configuration.
    _online = None                # Should we talk to the configured OpenSubmit server? 

    submission_url = None         # Download source for the student file / archive
    validator_url = None          # Download source for the validator file / archive
    working_dir = None            # The working directory for this job
    timeout = None                # The timeout for execution, as demanded by the server
    submission_id = None          # The OpenSubmit submission ID
    file_id = None                # The OpenSubmit submission file ID

    # The base name of the validation / full test script on disk, for importing.
    validator_import_name = 'validator'

    @property
    # The file name of the validation / full test script on disk, after unpacking / renaming.
    def validator_script_name(self):
        return self.working_dir + self.validator_import_name + '.py'

    def __init__(self, config = None, online = True):
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

    def run(self):
        '''
        Execute the validate() method in the test script belonging to this job.
        '''
        assert(os.path.exists(self.validator_script_name))
        old_path = sys.path
        sys.path = [self.working_dir] + old_path
        logger.debug('Python search path is now {0}.'.format(sys.path))
        module = importlib.import_module(self.validator_import_name)

        # Looped validator loading in the test suite demands this
        importlib.reload(module)

        # make the call
        module.validate(self)

        # roll back
        sys.path = old_path

    def send_result(self, result):
        '''
        Send test result to the OpenSubmit server.
        '''
        if result:
            post_data = [("SubmissionFileId",self.file_id),
                        ("Message", result.info_student),
                        ("MessageTutor", result.info_tutor),
                        ("ExecutorDir", self.working_dir),
                        ("ErrorCode", result.error_code),
                        ("Secret", self._config.get("Server","secret")),
                        ("UUID", self._config.get("Server","uuid"))
                        ]
            logger.debug('Sending result to OpenSubmit Server: '+str(post_data))
            if self._online:
                server.send(self._config, "/jobs/", post_data)
        else:
            logger.debug('Result is empty, nothing to send.')


    def delete_binaries(self):
        '''
        Scans the submission files in the self.working_dir for binaries and deletes them.
        Returns the list of deleted files.
        '''
        pass

    def run_configure(self, mandatory=True):
        '''
        Runs the configure tool configured for the machine in self.working_dir.
        Returns a CompletedProcess object.
        '''
        pass

    def run_make(self, mandatory=True):
        '''
        Runs the make tool configured for the machine in self.working_dir.
        Returns a CompletedProcess object.
        '''
        logger.debug("Running make ...")
        return call_make(self.working_dir)

    def run_compiler(self, compiler=GCC, output=None, inputs=None):
        '''
        Runs the compiler in self.working_dir.

        Returns a Result object.
        '''
        logger.debug("Running compiler ...")
        return call_compiler(self.working_dir, compiler, output, inputs)

    def run_binary(self, args, timeout, exclusive=False):
        '''
        Runs something from self.working_dir in a shell.
        The caller can demand exclusive execution on this machine.
        Returns a CompletedProcess object.
        '''
        pass

    def find_keywords(self, keywords, filepattern):
        '''
        Searches self.working_dir for files containing specific keywords.
        Expects a list of keywords to be searched for and the file pattern (*.c)
        as parameters.
        Returns the names of the files containing all of the keywords.
        '''
        pass

    def ensure_files(self, filenames):
        '''
        Searches the student submission for specific files.
        Expects a list of filenames.

        Returns a Result object.
        '''
        logger.debug("Testing {0} for the following files: {1}".format(self.working_dir, filenames))
        dircontent = os.listdir(self.working_dir)
        for fname in filenames:
            if fname not in dircontent:
                return FailResult("The file %s is missing."%fname)
        return PassResult("All files found: "+','.join(filenames))

