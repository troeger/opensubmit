from subprocess import CompletedProcess

from .result import Result, PassResult
from .filesystem import unpack_if_needed

class Submission():
    '''
        A student submission to be validated.
    '''
    _config = None

    download_file:str = None            # Submission file as provided by the student
    working_dir:str = None              # The working directory with the submission files.
    submission_id:str = None            # The OpenSubmit submission ID
    submission_file_id:str=None         # The OpenSubmit submission file ID
    timeout:int=None                    # The timeout for execution, as reported by the server

    def __init__(self):
        self._config=read_config()

    def __init__(self, config):
        self._config=config

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def __str__(self):
        return str(vars(self))

    def delete_binaries(self) -> tuple:
        '''
        Scans the submission files in the self.working_dir for binaries and deletes them.
        Returns the list of deleted files.
        '''
        pass

    def run_configure(self) -> CompletedProcess:
        '''
        Runs the configure tool configured for the machine in self.working_dir.
        '''
        pass

    def run_make(self) -> CompletedProcess:
        '''
        Runs the make tool configured for the machine in self.working_dir.
        '''
        pass

    def run_compiler(self) -> CompletedProcess:
        '''
        Runs the compiler configured for the machine in self.working_dir.
        '''
        pass

    def run_binary(self, args, timeout, exclusive=False) -> CompletedProcess:
        '''
        Runs something from self.working_dir in a shell.
        The caller can demand exclusive execution on this machine.
        '''
        pass

    def find_keywords(self, keywords, filepattern) -> tuple:
        '''
        Searches self.working_dir for files containing specific keywords.
        Expects a list of keywords to be searched for and the file pattern (*.c)
        as parameters.
        Returns the names of the files containing all of the keywords.
        '''
        pass

    def find_files(self, filenames) -> bool:
        '''
        Searches the student submission for specific files.
        Expects a list of filenames.
        Returns True if all file names exist in the submission.
        '''
        pass

    def has_files(self) -> None:
        '''
        Check if the student submission has any files.
        '''
        dircontent = os.listdir(self.working_dir)
        return len(dircontent) > 0

    def prepare(self) -> Result:
        '''
        Take the downloaded student submission file and prepare it for validation.     
        Return FailResult (to be returned to server) or PassResult object. 
        '''
        # Unpack archive
        numfiles = unpack_if_needed(self.working_dir, self.download_file)
        # Check number and kind of files in archive
        if numfiles is 0:
            logger.debug("Student archive is empty, notification about this stored as validation result.")
            return FailResult("Your compressed upload is empty - no files in there.")
        elif numfiles == 1 and os.path.isdir(self.working_dir + dircontent[0] + os.sep):
            logger.warning("The student archive contains only the directory %s. I assume I should go in there ..." % (dircontent[0]))
            self.working_dir = self.working_dir + dircontent[0] + os.sep
        # We are now definitely inside the right directory
        self.validator='validator.py'            #TODO: Should come with the request
        return PassResult(None)

    def send_result(self, result: Result) -> None:
        '''
        Send result to OpenSubmit server.
        '''
        from .server import send_result
        send_result(self, result)
