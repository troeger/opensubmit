from subprocess import CompletedProcess

from .result import Result, PassResult
from .filesystem import unpack_if_needed

class Submission():
    '''
        A student submission to be validated.
    '''
    _config = None

    sub_id = None                   # The OpenSubmit submission ID
    file_id = None                  # The OpenSubmit submission file ID

    def __init__(self):
        self._config = read_config()

    def __init__(self, config):
        self._config = config

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def __str__(self):
        return str(vars(self))

    def delete_binaries(self):
        '''
        Scans the submission files in the self.working_dir for binaries and deletes them.
        Returns the list of deleted files.
        '''
        pass

    def run_configure(self):
        '''
        Runs the configure tool configured for the machine in self.working_dir.
        Returns a CompletedProcess object.
        '''
        pass

    def run_make(self):
        '''
        Runs the make tool configured for the machine in self.working_dir.
        Returns a CompletedProcess object.
        '''
        pass

    def run_compiler(self):
        '''
        Runs the compiler configured for the machine in self.working_dir.
        Returns a CompletedProcess object.
        '''
        pass

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

    def find_files(self, filenames):
        '''
        Searches the student submission for specific files.
        Expects a list of filenames.
        Returns True if all file names exist in the submission.
        '''
        pass

    def has_files(self):
        '''
        Check if the student submission has any files.
        '''
        pass
